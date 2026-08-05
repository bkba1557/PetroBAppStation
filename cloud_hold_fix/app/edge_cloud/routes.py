from functools import wraps
import hashlib
import hmac
import json
import os
import base64
from decimal import Decimal
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from uuid import uuid4

from flask import Blueprint, abort, current_app, jsonify, redirect, render_template, request, session, url_for
from sqlalchemy import func, inspect, select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.core.roles import normalize_role
from app.core.tenant import current_company_id
from app.edge_cloud.services import EdgeError, EdgeService
from app.iam.service import has_permission
from app.extensions import get_session
from app.models import (
    Company, EdgeActivation, EdgeAuditLog, EdgeCertificate, EdgeDevice,
    EdgeDeviceEvent, EdgeHeartbeat, EdgePairingSession, Station,
    EdgeSerialPort, EdgePortInventorySync, CloudBusDevice,
    DeviceConfigurationVersion, EdgeConfigurationDelivery, ProtocolProfile, ProtocolVersion,
    DeviceProtocolAssignment, DeviceDeploymentPlan, EdgeProtocolDelivery,
    EdgeInstalledProtocol, EdgeIngestedEvent, DeviceReadingSnapshot, Probe, Tank,
    DeviceDeploymentEvent, ConfigurationSigningKey, EdgeRequestNonce, utcnow,
    EdgeContract, EdgeContractVersion, EdgeContractDelivery,
    HardwareActivationDelivery, HardwareDiagnosticRun,
    CalibrationDelivery, CalibrationInternalEvent, CalibrationPackageVersion, SaleTransaction, Pump, Nozzle,
    ShiftSession, PumpCommand, FuelingSession, CustomerAuditEvent, CustomerRealtimeEvent,
    CustomerWallet, WalletHold, WalletTransaction,
)
from app.edge_cloud.config_signing import ConfigurationSigningService, ConfigurationSigningError, canonical_bytes
from app.edge_cloud.deployment import DeviceDeploymentError, DeviceDeploymentOrchestrator
from app.edge_cloud.reconciliation import DeviceDeploymentReconciliationService
from app.edge_cloud.materialization import DesiredStateMaterializationService
from app.edge_cloud.contracts import (
    ContractControlError,
    EdgeContractReconciliationService,
    EdgeContractService,
    HardwareActivationService,
    is_non_expanding_revision,
)

edge_cloud = Blueprint("edge_cloud", __name__)


def _contract_signer():
    return ConfigurationSigningService(
        current_app.config["CONFIG_SIGNING_PRIVATE_KEY_FILE"],
        current_app.config["CONFIG_SIGNING_PUBLIC_KEY_FILE"],
        current_app.config["CONFIG_SIGNING_KEY_ID"],
    )


def correlation_id():
    return request.headers.get("X-Correlation-ID") or str(uuid4())


def _release_rejected_fueling_hold(db, fueling, delivery):
    """Release funds only when Edge rejected authorization before execution.

    A FAILED delivery may have crossed the serial execution boundary, so it is
    intentionally excluded until physical non-dispensing is proven. REJECTED
    is produced during command verification and therefore has no hardware TX.
    """
    if (
        delivery.action != "AUTHORIZE_FUELING_PRESET"
        or delivery.status != "REJECTED"
        or fueling is None
        or fueling.hold_id is None
        or fueling.wallet_id is None
    ):
        return False
    hold = db.get(WalletHold, fueling.hold_id)
    wallet = db.scalar(
        select(CustomerWallet)
        .where(CustomerWallet.id == fueling.wallet_id)
        .with_for_update()
    )
    if hold is None or wallet is None or hold.status != "HELD":
        return False
    amount = Decimal(str(hold.amount))
    reserved = Decimal(str(wallet.reserved_balance))
    available_before = Decimal(str(wallet.balance)) - reserved
    wallet.reserved_balance = max(Decimal("0"), reserved - amount)
    wallet.version += 1
    hold.status = "RELEASED"
    hold.released_at = utcnow()
    db.add(
        WalletTransaction(
            company_id=fueling.company_id,
            wallet_id=wallet.id,
            transaction_type="HOLD_RELEASE",
            amount=amount,
            balance_before=available_before,
            balance_after=available_before + amount,
            reference=hold.public_id,
            idempotency_key=f"release:hardware-rejected:{delivery.delivery_id}",
            metadata_json={
                "hold_id": hold.public_id,
                "fueling_session_id": fueling.public_id,
                "hardware_delivery_id": delivery.delivery_id,
                "reason": delivery.error_code or "EDGE_COMMAND_REJECTED",
            },
        )
    )
    return True


def service():
    secret = current_app.config.get("SECRET_KEY") or current_app.config.get("UNIFIED_SECRET")
    if not secret: secret = "TEST_ONLY_EDGE_SECRET" if current_app.config.get("TESTING") else None
    if not secret: raise RuntimeError("edge cloud secret is required")
    return EdgeService(get_session(), str(secret))


def edge_schema_ready():
    try:
        return inspect(get_session().get_bind()).has_table("edge_devices")
    except Exception:
        return False


def require_edge_schema():
    if not edge_schema_ready():
        raise EdgeError(
            "EDGE_SCHEMA_NOT_READY",
            "Edge device database migration 0022_edge_cloud_management has not been applied",
            503,
            True,
        )


def response(payload, status=200):
    result = jsonify(payload); result.status_code = status
    result.headers["X-Correlation-ID"] = correlation_id()
    return result


def _is_expired(value):
    if value is None:
        return False
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value <= utcnow()


EDGE_OFFLINE_AFTER_SECONDS = int(os.getenv("NNEXORIS_EDGE_OFFLINE_AFTER_SECONDS", "90"))


def _effective_connectivity(device, now=None):
    """Never display a stored ONLINE value after heartbeats have stopped."""
    now = now or utcnow()
    if device.last_seen_at is None:
        return "OFFLINE"
    last_seen = device.last_seen_at
    if last_seen.tzinfo is None:
        last_seen = last_seen.replace(tzinfo=timezone.utc)
    age = max(0.0, (now - last_seen).total_seconds())
    if age > EDGE_OFFLINE_AFTER_SECONDS:
        return "OFFLINE"
    if age > EDGE_OFFLINE_AFTER_SECONDS / 2:
        return "DEGRADED"
    return "ONLINE"


@edge_cloud.errorhandler(EdgeError)
def edge_error(error):
    get_session().rollback()
    return response({"code": error.code, "message": str(error), "retryable": error.retryable,
                     "correlation_id": correlation_id()}, error.status)


def require_permission(code):
    def decorator(fn):
        @wraps(fn)
        def wrapped(*args, **kwargs):
            if not has_permission(code): abort(403)
            return fn(*args, **kwargs)
        return wrapped
    return decorator


def device_for_user(device_id):
    device = get_session().get(EdgeDevice, device_id)
    if not device: abort(404)
    if normalize_role(session.get("unified_role")) != "Super Admin" and device.company_id != current_company_id():
        abort(404)
    return device


def serialize_device(device, sensitive=False):
    data = {"id": device.id, "device_uuid": device.device_uuid, "registration_number": device.registration_number,
        "name": device.name, "company_id": device.company_id, "station_id": device.station_id,
        "status": device.status, "connectivity_status": _effective_connectivity(device), "health_status": device.health_status,
        "last_seen_at": device.last_seen_at.isoformat() if device.last_seen_at else None,
        "edge_version": device.edge_version, "configuration_version": device.configuration_version,
        "outbox_pending_count": device.outbox_pending_count, "failed_commands_count": device.failed_commands_count,
        "activated_at": device.activated_at.isoformat() if device.activated_at else None}
    company = get_session().get(Company, device.company_id) if device.company_id else None
    station = get_session().get(Station, device.station_id) if device.station_id else None
    heartbeat = get_session().scalar(select(EdgeHeartbeat).where(
        EdgeHeartbeat.device_id == device.id).order_by(EdgeHeartbeat.received_at.desc()))
    data.update(
        company={"id": company.id, "name_ar": company.name_ar, "name_en": company.name_en} if company else None,
        station={"id": station.id, "name_ar": station.name_ar, "name_en": station.name_en} if station else None,
        latest_telemetry=_serialize_heartbeat(heartbeat) if heartbeat else None,
    )
    ports = get_session().scalars(select(EdgeSerialPort).where(
        EdgeSerialPort.edge_device_id == device.id)).all()
    bus_devices = get_session().scalars(select(CloudBusDevice).where(
        CloudBusDevice.edge_device_id == device.id)).all()
    data.update(
        ports_total=len(ports),
        ports_available=sum(row.status == "AVAILABLE" for row in ports),
        ports_busy=sum(row.status == "BUSY_EXTERNAL" for row in ports),
        linked_devices_count=len(bus_devices),
        protocol_sync="VERIFIED" if bus_devices and all(
            row.protocol_version_id and get_session().scalar(select(EdgeInstalledProtocol.id).where(
                EdgeInstalledProtocol.edge_device_id == device.id,
                EdgeInstalledProtocol.protocol_version_id == row.protocol_version_id,
                EdgeInstalledProtocol.definition_hash == row.protocol_hash,
                EdgeInstalledProtocol.status == "VERIFIED",
            )) for row in bus_devices) else ("NO DEVICES" if not bus_devices else "PENDING"),
        offline_ready=bool(bus_devices) and all(row.offline_ready for row in bus_devices),
    )
    if sensitive:
        data.update(public_key_fingerprint=device.public_key_fingerprint, hardware=device.hardware_json,
                    operating_system=device.operating_system_json, hostname=device.hostname)
    return data


def _metric(payload, *names):
    sources = [payload.get("telemetry"), payload.get("metrics"), payload.get("health"), payload]
    for source in sources:
        if not isinstance(source, dict):
            continue
        for name in names:
            if source.get(name) is not None:
                return source[name]
    return None


def _serialize_heartbeat(row):
    payload = row.payload_json_filtered or {}
    return {
        "sequence": row.sequence,
        "sent_at": row.sent_at.isoformat(),
        "received_at": row.received_at.isoformat(),
        "health_status": row.health_status,
        "cpu_percent": row.cpu_percent,
        "cpu_temperature_c": row.temperature,
        "load_average_1m": _metric(payload, "load_average_1m", "load_1m"),
        "load_average_5m": _metric(payload, "load_average_5m", "load_5m"),
        "load_average_15m": _metric(payload, "load_average_15m", "load_15m"),
        "memory_percent": row.memory_percent,
        "memory_total_bytes": _metric(payload, "memory_total_bytes", "memory_total"),
        "memory_used_bytes": _metric(payload, "memory_used_bytes", "memory_used"),
        "memory_available_bytes": _metric(payload, "memory_available_bytes", "memory_available"),
        "disk_percent": row.disk_percent,
        "disk_total_bytes": _metric(payload, "disk_total_bytes", "disk_total"),
        "disk_used_bytes": _metric(payload, "disk_used_bytes", "disk_used"),
        "disk_free_bytes": _metric(payload, "disk_free_bytes", "disk_available_bytes", "disk_free"),
        "uptime_seconds": row.uptime_seconds,
        "latency_ms": _metric(payload, "latency_ms", "cloud_latency_ms"),
    }


@edge_cloud.post("/api/v1/edge/pairing/sessions")
def enrollment():
    require_edge_schema()
    if request.content_length and request.content_length > 262_144:
        raise EdgeError("PAYLOAD_TOO_LARGE", "maximum enrollment payload is 256 KiB", 413)
    return response(service().enroll(request.get_json(force=True), request.headers.get("Idempotency-Key"),
        correlation_id(), request.remote_addr), 201)


@edge_cloud.post("/api/v1/edge/enrollment")
def enrollment_alias():
    return enrollment()


@edge_cloud.get("/api/v1/edge/pairing/status")
def pairing_status():
    require_edge_schema()
    return response(service().pairing_status(
        request.args.get("pairing_session_id"), correlation_id()))


@edge_cloud.post("/api/v1/edge/pairing/confirm")
def pairing_confirm():
    body = request.get_json(force=True)
    if body.get("local_confirmation") is not True:
        raise EdgeError("LOCAL_CONFIRMATION_REQUIRED", "local_confirmation must be true", 422)
    return response(service().local_confirm(body["pairing_session_id"], body["request_identifier"], correlation_id()))


@edge_cloud.post("/api/v1/edge/activation")
def activation_download():
    body = request.get_json(force=True)
    result = service().retrieve_activation(body, request.headers.get("Idempotency-Key"), correlation_id())
    try:
        result["cloud_configuration_signing_keys"] = [ConfigurationSigningService(
            current_app.config["CONFIG_SIGNING_PRIVATE_KEY_FILE"],
            current_app.config["CONFIG_SIGNING_PUBLIC_KEY_FILE"],
            current_app.config["CONFIG_SIGNING_KEY_ID"],
        ).public_metadata()]
    except ConfigurationSigningError:
        result["cloud_configuration_signing_keys"] = []
    return response(result)


@edge_cloud.post("/api/v1/edge/activation/acknowledge")
def activation_acknowledge():
    body = request.get_json(force=True)
    if "device_proof" in body:
        return response(service().confirm_activation(body, correlation_id()))
    allow_legacy = current_app.config.get("TESTING") or (
        os.getenv("PETROB_EDGE_ALLOW_LEGACY_ACTIVATION_IN_SHADOW", "false").lower() == "true"
        and current_app.config.get("DEVICE_IO_ENABLED") is False
    )
    if not allow_legacy:
        raise EdgeError("DEVICE_PROOF_INVALID", "signed activation confirmation is required", 401)
    return response(service().acknowledge(
        body["registration_number"], body["activation_token"], correlation_id()))


@edge_cloud.post("/api/v1/edge/activation/confirm")
def activation_confirm():
    return response(service().confirm_activation(request.get_json(force=True), correlation_id()))


@edge_cloud.post("/api/v1/edge/heartbeat")
def heartbeat():
    if request.content_length and request.content_length > 131_072:
        raise EdgeError("PAYLOAD_TOO_LARGE", "maximum heartbeat payload is 128 KiB", 413)
    allow_unsigned = current_app.config.get("TESTING") or (
        os.getenv("PETROB_EDGE_ALLOW_UNSIGNED_HEARTBEAT_IN_SHADOW", "false").lower() == "true"
        and current_app.config.get("DEVICE_IO_ENABLED") is False
    )
    return response(service().heartbeat(request.get_json(force=True), allow_unsigned=allow_unsigned))


@edge_cloud.post("/api/v1/edge/pumps/live")
def pump_live():
    body = request.get_json(force=True)
    device = get_session().scalar(select(EdgeDevice).where(
        EdgeDevice.device_uuid == body.get("edge_device_uuid")
    ))
    if device is None:
        raise EdgeError("DEVICE_UNKNOWN", "Edge device not found", 404)
    _require_edge_proof(device, body)
    runtime = body.get("pump_runtime")
    if not isinstance(runtime, dict) or not isinstance(runtime.get("hoses"), list):
        raise EdgeError("PUMP_LIVE_SCHEMA_INVALID", "pump runtime snapshot is invalid", 422)
    now = utcnow()
    service().persist_pump_runtime(device, body, now)
    get_session().commit()
    return response({"status": "ACCEPTED", "received_at": now.isoformat()})


def _inventory_message(body):
    safe = {key: value for key, value in body.items() if key != "device_proof"}
    return ("NNEXORIS-PORT-INVENTORY-V1\n" + json.dumps(
        safe, sort_keys=True, separators=(",", ":"), default=str
    )).encode()


def _require_edge_identity(device, body):
    if body.get("edge_device_uuid") != device.device_uuid:
        raise EdgeError("EDGE_IDENTITY_MISMATCH", "inventory does not belong to this Edge", 403)
    _require_edge_proof(device, body)


def _proof_body(body):
    return {k: v for k, v in body.items() if k not in {"device_proof", "body_hash"}}


def _require_edge_proof(device, body, db=None):
    if (
        device.status != "ACTIVE"
        or device.activated_at is None
        or device.suspended_at is not None
        or device.revoked_at is not None
        or device.deleted_at is not None
    ):
        raise EdgeError("EDGE_NOT_ACTIVE", "an active Edge device is required", 403)
    proof = body.get("device_proof")
    timestamp, nonce, request_id, body_hash = body.get("timestamp"), body.get("nonce"), body.get("request_id"), body.get("body_hash")
    if not all(isinstance(x, str) and x for x in (timestamp, nonce, request_id, body_hash)):
        raise EdgeError("DEVICE_PROOF_INVALID", "timestamp, nonce, request_id and body_hash are required", 401)
    actual_hash = hashlib.sha256(canonical_bytes(_proof_body(body))).hexdigest()
    if not hmac.compare_digest(actual_hash, body_hash):
        raise EdgeError("DEVICE_PROOF_INVALID", "request body hash is invalid", 401)
    try:
        sent_at = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except ValueError as exc:
        raise EdgeError("REQUEST_TIMESTAMP_INVALID", "timestamp is invalid", 401) from exc
    if abs((utcnow() - sent_at).total_seconds()) > int(current_app.config.get("EDGE_PROOF_MAX_CLOCK_SKEW_SECONDS", 300)):
        raise EdgeError("REQUEST_TIMESTAMP_INVALID", "request outside accepted time window", 401)
    db = db or get_session(); operation = request.path
    duplicate = db.scalar(select(EdgeRequestNonce).where(EdgeRequestNonce.device_id == device.id,
        EdgeRequestNonce.operation == operation, EdgeRequestNonce.nonce == nonce))
    if duplicate or db.scalar(select(EdgeRequestNonce).where(EdgeRequestNonce.device_id == device.id, EdgeRequestNonce.request_id == request_id)):
        raise EdgeError("NONCE_REPLAYED", "request nonce or request id was already used", 409)
    message = ("NNEXORIS-EDGE-PROOF-V1\n" + json.dumps({"method": request.method.upper(), "path": request.path,
        "edge_device_uuid": device.device_uuid, "timestamp": timestamp, "nonce": nonce,
        "request_id": request_id, "body_hash": body_hash}, sort_keys=True, separators=(",", ":"))).encode()
    service()._verify_device_proof(device, proof, message)
    db.add(EdgeRequestNonce(device_id=device.id, operation=operation, nonce=nonce,
        request_id=request_id, request_method=request.method.upper(), request_path=request.path,
        body_hash=body_hash, expires_at=utcnow() + timedelta(seconds=int(current_app.config.get("EDGE_PROOF_NONCE_TTL_SECONDS", 600)))))


@edge_cloud.post("/api/v1/edge/trust/configuration-signing-keys")
def configuration_signing_keys():
    require_edge_schema()
    body = request.get_json(force=True)
    device = get_session().scalar(
        select(EdgeDevice).where(
            EdgeDevice.device_uuid == body.get("edge_device_uuid")
        )
    )
    if not device:
        raise EdgeError("DEVICE_UNKNOWN", "Edge device not found", 404)
    _require_edge_proof(device, body)
    try:
        metadata = ConfigurationSigningService(
            current_app.config["CONFIG_SIGNING_PRIVATE_KEY_FILE"],
            current_app.config["CONFIG_SIGNING_PUBLIC_KEY_FILE"],
            current_app.config["CONFIG_SIGNING_KEY_ID"],
        ).public_metadata()
    except ConfigurationSigningError as exc:
        raise EdgeError(str(exc), "configuration signing is unavailable", 503) from exc
    if metadata["algorithm"] != "Ed25519":
        raise EdgeError("CONFIG_SIGNING_ALGORITHM_INVALID", "Ed25519 is required", 503)
    key_row = get_session().scalar(
        select(ConfigurationSigningKey).where(
            ConfigurationSigningKey.key_id == metadata["key_id"],
            ConfigurationSigningKey.status == "ACTIVE",
        )
    )
    if (
        key_row is None
        or key_row.revoked_at is not None
        or key_row.fingerprint_sha256 != metadata["fingerprint_sha256"]
        or key_row.public_key != metadata["public_key"]
    ):
        raise EdgeError(
            "CONFIG_SIGNING_KEY_METADATA_MISMATCH",
            "active configuration signing key metadata is unavailable",
            503,
        )
    get_session().add(
        EdgeAuditLog(
            device_id=device.id,
            company_id=device.company_id,
            action="edge.trust.configuration_signing_keys",
            old_values={},
            new_values={
                "key_id": metadata["key_id"],
                "fingerprint_sha256": metadata["fingerprint_sha256"],
            },
            correlation_id=correlation_id(),
            ip_address=request.remote_addr,
        )
    )
    get_session().commit()
    return response(
        {
            "edge_device_uuid": device.device_uuid,
            "keys": [
                {
                    **metadata,
                    "valid_from": key_row.valid_from.isoformat(),
                    "valid_until": (
                        key_row.valid_until.isoformat() if key_row.valid_until else None
                    ),
                }
            ],
        }
    )


def _port_json(row):
    assigned = get_session().scalar(
        select(func.count()).select_from(CloudBusDevice).where(CloudBusDevice.serial_port_id == row.id)
    ) or 0
    return {
        "id": row.id, "edge_device_id": row.edge_device_id, "company_id": row.company_id,
        "station_id": row.station_id, "stable_identity": row.stable_identity,
        "by_id_path": row.by_id_path, "by_path": row.by_path,
        "resolved_device": row.resolved_device, "vendor": row.vendor, "model": row.model,
        "vendor_id": row.vendor_id, "product_id": row.product_id, "serial_number": row.serial_number,
        "driver": row.driver, "physical_path": row.physical_path, "status": row.status,
        "ownership_status": row.ownership_status, "owner_process": row.owner_process,
        "owner_pid": row.owner_pid, "owner_service": row.owner_service,
        "capabilities": row.capabilities_json, "metadata": row.metadata_json,
        "first_seen_at": row.first_seen_at.isoformat(), "last_seen_at": row.last_seen_at.isoformat(),
        "disconnected_at": row.disconnected_at.isoformat() if row.disconnected_at else None,
        "friendly_name": row.friendly_name, "function": row.function_label,
        "current_tty": row.resolved_device, "usb_serial": row.serial_number,
        "vid": row.vendor_id, "pid": row.product_id, "usb_physical_path": row.physical_path,
        "external_owner": row.owner_service or row.owner_process,
        "assigned_devices_count": assigned,
    }


def _device_json(row):
    port = get_session().get(EdgeSerialPort, row.serial_port_id)
    version = get_session().get(DeviceConfigurationVersion, row.last_configuration_version_id) if row.last_configuration_version_id else None
    edge = get_session().get(EdgeDevice, row.edge_device_id)
    return {
        "id": row.id, "uuid": row.cloud_device_id, "name": row.device_name,
        "device_type": row.device_type, "company_id": row.company_id, "station_id": row.station_id,
        "edge": {"id": edge.id, "uuid": edge.device_uuid} if edge else None,
        "port": _port_json(port) if port else None,
        "protocol_code": row.protocol_code, "protocol_version": row.protocol_version,
        "protocol_hash": row.protocol_hash, "address": row.device_address,
        "deployment_status": row.deployment_status,
        "configuration_status": row.configuration_status,
        "activation_status": row.activation_status,
        "activation_blocked_reason": row.activation_blocked_reason,
        "offline_ready": row.offline_ready, "hardware_active": row.hardware_active,
        "last_configuration_version": version.version_number if version else None,
        "last_configuration_version_id": row.last_configuration_version_id,
        "last_delivery_id": row.last_delivery_id, "last_delivery_status": row.configuration_status,
        "last_edge_ack_at": row.last_edge_ack_at.isoformat() if row.last_edge_ack_at else None,
        "last_seen": port.last_seen_at.isoformat() if port else None,
    }


@edge_cloud.post("/api/v1/edge/devices/<int:edge_device_id>/serial-ports/sync")
def serial_ports_sync(edge_device_id):
    require_edge_schema()
    body = request.get_json(force=True)
    ports = body.get("ports")
    if not isinstance(ports, list) or len(ports) > 256:
        raise EdgeError("INVENTORY_INVALID", "ports must be an array of at most 256 items", 422)
    device = get_session().get(EdgeDevice, edge_device_id)
    if not device:
        raise EdgeError("DEVICE_UNKNOWN", "Edge device not found", 404)
    _require_edge_identity(device, body)
    sync_id = str(body.get("sync_id", "")).strip()
    if not sync_id:
        raise EdgeError("SYNC_ID_REQUIRED", "sync_id is required", 422)
    existing = get_session().scalar(select(EdgePortInventorySync).where(
        EdgePortInventorySync.edge_device_id == device.id, EdgePortInventorySync.sync_id == sync_id))
    if existing:
        return response({"accepted": True, "sync_id": sync_id, "inventory_version": existing.inventory_version,
                         "received_ports": existing.port_count, "updated_ports": existing.port_count,
                         "disconnected_ports": 0, "idempotent": True, "server_time": utcnow().isoformat()})
    checksum = hashlib.sha256(json.dumps(ports, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()
    seen = set(); updated = 0
    for item in ports:
        stable = str(item.get("stable_identity", "")).strip()
        if not stable or len(stable) > 512 or stable in seen:
            raise EdgeError("INVENTORY_INVALID", "stable_identity is required and unique per inventory", 422)
        seen.add(stable)
        row = get_session().scalar(select(EdgeSerialPort).where(
            EdgeSerialPort.edge_device_id == device.id, EdgeSerialPort.stable_identity == stable))
        if row is None:
            row = EdgeSerialPort(edge_device_id=device.id, company_id=device.company_id, station_id=device.station_id,
                stable_identity=stable, first_seen_at=utcnow(), last_seen_at=utcnow(),
                capabilities_json=list(item.get("capabilities") or []), metadata_json=dict(item.get("metadata") or {}),
                status=str(item.get("status", "AVAILABLE")), ownership_status=str(item.get("ownership_status", "FREE")))
            get_session().add(row)
        for source, target in (("by_id_path", "by_id_path"), ("by_path", "by_path"), ("resolved_device", "resolved_device"),
            ("vendor", "vendor"), ("model", "model"), ("vendor_id", "vendor_id"), ("product_id", "product_id"),
            ("serial_number", "serial_number"), ("driver", "driver"), ("physical_path", "physical_path"),
            ("status", "status"), ("ownership_status", "ownership_status"), ("owner_process", "owner_process"),
            ("owner_pid", "owner_pid"), ("owner_service", "owner_service")):
            if source in item: setattr(row, target, item[source])
        row.company_id, row.station_id, row.last_seen_at, row.disconnected_at = device.company_id, device.station_id, utcnow(), None
        row.capabilities_json, row.metadata_json = list(item.get("capabilities") or []), dict(item.get("metadata") or {})
        updated += 1
    disconnected = 0
    for row in get_session().scalars(select(EdgeSerialPort).where(EdgeSerialPort.edge_device_id == device.id)).all():
        if row.stable_identity not in seen and row.status != "DISCONNECTED":
            row.status, row.disconnected_at = "DISCONNECTED", utcnow(); disconnected += 1
    sync = EdgePortInventorySync(edge_device_id=device.id, sync_id=sync_id,
        inventory_version=int(body.get("inventory_version", 0)), port_count=len(ports), checksum=checksum)
    get_session().add(sync)
    get_session().add(EdgeAuditLog(device_id=device.id, company_id=device.company_id, action="edge.serial_inventory.sync",
        old_values={}, new_values={"sync_id": sync_id, "port_count": len(ports)}, correlation_id=correlation_id(), ip_address=request.remote_addr))
    get_session().commit()
    return response({"accepted": True, "sync_id": sync_id, "inventory_version": sync.inventory_version,
        "received_ports": len(ports), "updated_ports": updated, "disconnected_ports": disconnected,
        "server_time": utcnow().isoformat()})


@edge_cloud.get("/api/v1/edge-devices/<int:device_id>/serial-ports")
@require_permission("edge.device.view")
def serial_ports_list(device_id):
    device = device_for_user(device_id)
    query = select(EdgeSerialPort).where(EdgeSerialPort.edge_device_id == device.id)
    if request.args.get("status"): query = query.where(EdgeSerialPort.status == request.args["status"])
    rows = get_session().scalars(query.order_by(EdgeSerialPort.stable_identity)).all()
    return response({"items": [_port_json(row) for row in rows], "total": len(rows)})


@edge_cloud.get("/api/v1/edge-devices/<int:device_id>/serial-ports/<int:port_id>/devices")
@require_permission("edge.device.view")
def serial_port_devices(device_id, port_id):
    device_for_user(device_id)
    rows = get_session().scalars(select(CloudBusDevice).where(
        CloudBusDevice.edge_device_id == device_id, CloudBusDevice.serial_port_id == port_id)).all()
    return response({"items": [{"id": row.id, "cloud_device_id": row.cloud_device_id, "device_type": row.device_type,
        "device_name": row.device_name, "protocol_id": row.protocol_id, "device_address": row.device_address,
        "status": row.status} for row in rows]})


@edge_cloud.patch("/api/v1/edge-devices/<int:device_id>/serial-ports/<int:port_id>/presentation")
@require_permission("edge.device.update")
def serial_port_presentation(device_id, port_id):
    device = device_for_user(device_id)
    row = get_session().get(EdgeSerialPort, port_id)
    if not row or row.edge_device_id != device.id:
        abort(404)
    body = request.get_json(force=True)
    if "stable_identity" in body:
        raise EdgeError("STABLE_IDENTITY_IMMUTABLE", "stable identity cannot be edited", 422)
    allowed_functions = {"PUMPS", "TANKS", "PRICEBOARD", "RFID", "PAYMENT", "CONTROLLER", "SENSOR", "OTHER", None}
    friendly = body.get("friendly_name")
    function = body.get("function")
    if friendly is not None and (not isinstance(friendly, str) or len(friendly.strip()) > 160):
        raise EdgeError("FRIENDLY_NAME_INVALID", "friendly_name is invalid", 422)
    if function not in allowed_functions:
        raise EdgeError("FUNCTION_INVALID", "function label is invalid", 422)
    row.friendly_name = friendly.strip() if isinstance(friendly, str) and friendly.strip() else None
    row.function_label = function
    get_session().add(EdgeAuditLog(device_id=device.id, company_id=device.company_id,
        action="edge.serial_port.presentation.updated", old_values={},
        new_values={"port_id": row.id, "friendly_name": row.friendly_name, "function": row.function_label},
        correlation_id=correlation_id(), ip_address=request.remote_addr))
    get_session().commit()
    return response(_port_json(row))


@edge_cloud.get("/api/v1/edge-devices/<int:device_id>/devices")
@require_permission("edge.device.view")
def bus_devices_list(device_id):
    device_for_user(device_id)
    rows = get_session().scalars(select(CloudBusDevice).where(
        CloudBusDevice.edge_device_id == device_id).order_by(CloudBusDevice.id)).all()
    return response({"items": [_device_json(row) for row in rows], "total": len(rows)})


def _bus_device_for_user(device_id):
    row = get_session().get(CloudBusDevice, device_id)
    if not row:
        abort(404)
    device_for_user(row.edge_device_id)
    return row


@edge_cloud.get("/api/v1/devices/<int:device_id>")
@require_permission("edge.device.view")
def bus_device_detail(device_id):
    return response(_device_json(_bus_device_for_user(device_id)))


@edge_cloud.get("/api/v1/devices/<int:device_id>/deployment")
@require_permission("edge.device.view")
def bus_device_deployment(device_id):
    row = _bus_device_for_user(device_id)
    DeviceDeploymentReconciliationService(get_session()).reconcile_device(
        row.id, source="READ_RECONCILIATION"
    )
    get_session().commit()
    return response(_device_json(row))


@edge_cloud.get("/api/v1/devices/<int:device_id>/history")
@require_permission("edge.device.view_logs")
def bus_device_history(device_id):
    row = _bus_device_for_user(device_id)
    events = get_session().scalars(select(DeviceDeploymentEvent).where(
        DeviceDeploymentEvent.cloud_bus_device_id == row.id
    ).order_by(DeviceDeploymentEvent.occurred_at.desc())).all()
    return response({"items": [{
        "event_type": item.event_type, "source": item.source,
        "configuration_version_id": item.configuration_version_id,
        "delivery_id": item.delivery_id, "metadata": item.metadata_json,
        "occurred_at": item.occurred_at.isoformat(),
    } for item in events]})


def _canonical_configuration(payload):
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode()


@edge_cloud.post("/api/v1/edge-devices/<int:device_id>/port-configurations")
@require_permission("edge.device.update")
def create_port_configuration(device_id):
    device = device_for_user(device_id); body = request.get_json(force=True)
    forbidden = {"raw_frame", "frame", "shell", "executable", "command"}
    if forbidden.intersection(body):
        raise EdgeError("RAW_PAYLOAD_FORBIDDEN", "raw frames and executable payloads are not allowed", 422)
    required = {"serial_port_id", "company_id", "station_id", "device_type", "device_name", "protocol_id", "device_address"}
    if required - body.keys(): raise EdgeError("CONFIGURATION_INVALID", "required configuration field missing", 422)
    db = get_session(); port = db.get(EdgeSerialPort, int(body["serial_port_id"])); protocol = db.get(ProtocolProfile, int(body["protocol_id"]))
    if not port or port.edge_device_id != device.id: raise EdgeError("PORT_NOT_FOUND", "port is not assigned to this Edge", 404)
    if body.get("stable_identity") is not None and body.get("stable_identity") != port.stable_identity:
        raise EdgeError("PORT_IDENTITY_MISMATCH", "stable port identity does not match selected port", 409)
    if port.status in {"DISCONNECTED", "PERMISSION_DENIED", "ERROR"}: raise EdgeError("PORT_NOT_AVAILABLE", "port is not available", 409)
    if device.station_id != int(body["station_id"]) or device.company_id != int(body["company_id"]): raise EdgeError("TENANT_MISMATCH", "Edge assignment does not match station/company", 403)
    if not protocol or not protocol.enabled: raise EdgeError("PROTOCOL_INVALID", "protocol is not enabled", 422)
    assignment = db.scalar(select(DeviceProtocolAssignment).where(
        DeviceProtocolAssignment.edge_device_id == device.id,
        DeviceProtocolAssignment.protocol_profile_id == protocol.id,
        DeviceProtocolAssignment.active.is_(True),
    ))
    if assignment is None:
        assignment = DeviceProtocolAssignment(
            company_id=device.company_id, station_id=device.station_id,
            edge_device_id=device.id, device_category=str(body["device_type"]),
            protocol_profile_id=protocol.id,
            protocol_version_id=protocol.published_version_id,
            device_address=str(body["device_address"]),
            configuration_json={}, status="ASSIGNED",
            assigned_by_user_id=session.get("unified_user_id"),
            enabled=False, active=True,
        )
        db.add(assignment)
        db.flush()
    try:
        _, _, pinned_version = DeviceDeploymentOrchestrator(db).ensure_assignment(assignment)
    except DeviceDeploymentError as exc:
        raise EdgeError(str(exc), "published signed protocol dependency is required", 409) from exc
    installed = db.scalar(select(EdgeInstalledProtocol).where(
        EdgeInstalledProtocol.edge_device_id == device.id,
        EdgeInstalledProtocol.protocol_version_id == pinned_version.id,
        EdgeInstalledProtocol.definition_hash == pinned_version.definition_hash,
        EdgeInstalledProtocol.status == "VERIFIED",
    ))
    if installed is None:
        db.commit()
        raise EdgeError("WAITING_FOR_PROTOCOL", "protocol dependency must be verified before configuration delivery", 409)
    requested_version_id = body.get("protocol_version_id")
    if requested_version_id is not None and int(requested_version_id) != pinned_version.id:
        raise EdgeError("PROTOCOL_VERSION_MISMATCH", "device must use its pinned immutable protocol version", 409)
    definition = pinned_version.definition_json
    if definition.get("device_type") != body["device_type"]:
        raise EdgeError("PROTOCOL_DEVICE_TYPE_MISMATCH", "protocol is incompatible with device type", 422)
    address = str(body["device_address"]).removeprefix("0x").upper()
    address_schema = definition.get("address_schema", {})
    if not isinstance(address_schema, dict) or address not in {
        str(value).removeprefix("0x").upper()
        for value in address_schema.get("allowed_values", [])
    }:
        raise EdgeError("PROTOCOL_ADDRESS_INVALID", "address is outside the signed protocol schema", 422)
    bus_defaults = definition.get("bus_defaults")
    if not isinstance(bus_defaults, dict):
        raise EdgeError("PROTOCOL_BUS_SCHEMA_INVALID", "signed protocol has no bus defaults", 422)
    supplied_bus = body.get("bus_config", {})
    if not isinstance(supplied_bus, dict) or any(
        supplied_bus.get(name) != bus_defaults.get(name)
        for name in ("baudrate", "data_bits", "parity", "stop_bits", "timeout_ms")
    ):
        raise EdgeError("PROTOCOL_BUS_SETTINGS_MISMATCH", "bus settings must match the signed protocol version", 422)
    if body.get("command_permissions") != ["READ_STATUS"]:
        raise EdgeError("COMMAND_PERMISSION_POLICY_VIOLATION", "only READ_STATUS is permitted", 422)
    duplicate = db.scalar(select(CloudBusDevice).where(CloudBusDevice.edge_device_id == device.id, CloudBusDevice.serial_port_id == port.id,
        CloudBusDevice.protocol_id == protocol.id, CloudBusDevice.device_address == address))
    if duplicate: raise EdgeError("ADDRESS_CONFLICT", "device address already exists on this bus", 409)
    config = {"cloud_device_id": str(uuid4()), "company_id": int(body["company_id"]), "station_id": int(body["station_id"]),
        "edge_device_id": device.id, "serial_port_identity": port.stable_identity, "device_type": str(body["device_type"]),
        "device_name": str(body["device_name"]), "logical_number": body.get("logical_number"), "protocol_id": protocol.id,
        "protocol": protocol.code or str(protocol.id),
        "protocol_version_id": pinned_version.id,
        "protocol_version": pinned_version.version,
        "protocol_hash": pinned_version.definition_hash,
        "device_address": address,
        "bus_config": body.get("bus_config", {}), "protocol_config": body.get("protocol_config", {}),
        "capabilities": body.get("capabilities", []), "polling_config": body.get("polling_config", {}),
        "command_permissions": [p for p in body.get("command_permissions", []) if p in {"READ_STATUS", "READ_TOTALS", "READ_HEALTH"}]}
    bus = CloudBusDevice(cloud_device_id=config["cloud_device_id"], company_id=config["company_id"], station_id=config["station_id"], edge_device_id=device.id, serial_port_id=port.id, device_type=config["device_type"], device_name=config["device_name"], logical_number=config["logical_number"], protocol_id=protocol.id, protocol_version_id=pinned_version.id, protocol_code=protocol.code, protocol_version=pinned_version.version, protocol_hash=pinned_version.definition_hash, device_address=config["device_address"], bus_config_json=config["bus_config"], protocol_config_json=config["protocol_config"], capabilities_json=config["capabilities"], polling_config_json=config["polling_config"], command_permissions_json=config["command_permissions"], status="PENDING", created_by=session.get("unified_user_id"))
    db.add(bus); db.flush()
    version = DeviceConfigurationVersion(station_id=bus.station_id, device_category=bus.device_type,
        device_id=bus.id, version_number=1, configuration_json=config,
        changed_by=str(session.get("unified_user_id") or "cloud"),
        configuration_hash="", signature="", signature_algorithm="Ed25519", status="PENDING_DELIVERY",
        delivery_status="PENDING")
    db.add(version); db.flush()
    delivery = EdgeConfigurationDelivery(configuration_version_id=version.id, edge_device_id=device.id, delivery_id=str(uuid4()), status="PENDING", response_json={})
    issued = utcnow(); envelope = {"schema_version": 1, "delivery_id": delivery.delivery_id,
        "configuration_version_id": str(version.id), "configuration_version": 1,
        "edge_device_uuid": device.device_uuid, "station_id": str(device.station_id),
        "company_id": str(device.company_id), "issued_at": issued.isoformat(),
        "expires_at": (issued + timedelta(hours=1)).isoformat(), "configuration": config}
    try:
        signer = ConfigurationSigningService(current_app.config["CONFIG_SIGNING_PRIVATE_KEY_FILE"], current_app.config["CONFIG_SIGNING_PUBLIC_KEY_FILE"], current_app.config["CONFIG_SIGNING_KEY_ID"])
        signed = signer.sign(envelope)
        metadata = signer.public_metadata()
        key_row = db.scalar(select(ConfigurationSigningKey).where(ConfigurationSigningKey.key_id == metadata["key_id"]))
        if key_row is None:
            db.add(ConfigurationSigningKey(key_id=metadata["key_id"], algorithm=metadata["algorithm"], public_key=metadata["public_key"], private_key_reference=str(signer.private_path), fingerprint_sha256=metadata["fingerprint_sha256"], status="ACTIVE", metadata_json={}))
    except ConfigurationSigningError as exc:
        db.rollback(); raise EdgeError(str(exc), "configuration signing is unavailable", 503)
    version.configuration_json = signed["envelope"]; version.configuration_hash = signed["configuration_hash"]; version.signature = signed["signature"]; version.signing_key_id = signed["signing_key_id"]
    db.add(delivery); db.add(EdgeAuditLog(device_id=device.id, company_id=device.company_id, user_id=session.get("unified_user_id"), action="edge.configuration.staged", old_values={}, new_values={"cloud_device_id": bus.cloud_device_id, "version": 1}, correlation_id=correlation_id(), ip_address=request.remote_addr)); db.commit()
    return response({"status": "PENDING_DELIVERY", "cloud_device_id": bus.cloud_device_id, "configuration_version_id": version.id, "configuration_hash": version.configuration_hash, "signature_algorithm": "Ed25519", "signing_key_id": version.signing_key_id, "delivery_id": delivery.delivery_id}, 201)


def _protocol_package(delivery, version, profile):
    definition = version.definition_json
    device_type = definition.get("device_type")
    device_types = definition.get("supported_device_types") or (
        [device_type] if isinstance(device_type, str) else []
    )
    return {
        "protocol_delivery_id": delivery.delivery_id,
        "protocol_id": profile.id,
        "protocol_code": profile.code,
        "protocol_version_id": version.id,
        "version": version.version,
        "schema_version": definition.get("schema_version"),
        "device_types": device_types,
        "transport": definition.get("transport"),
        "definition_json": definition,
        "definition_hash": version.definition_hash,
        "envelope": version.signed_envelope_json,
        "signature": version.signature,
        "signature_algorithm": version.signature_algorithm,
        "signing_key_id": version.signing_key_id,
        "published_at": version.published_at.isoformat() if version.published_at else None,
        "status": version.status,
    }


@edge_cloud.post("/api/v1/edge/protocols/pull")
def protocol_pull():
    body = request.get_json(force=True)
    device = get_session().scalar(select(EdgeDevice).where(
        EdgeDevice.device_uuid == body.get("edge_device_uuid")
    ))
    if not device:
        raise EdgeError("DEVICE_UNKNOWN", "Edge device not found", 404)
    _require_edge_proof(device, body)
    installed = body.get("installed_protocols", [])
    if not isinstance(installed, list) or len(installed) > 256:
        raise EdgeError("PROTOCOL_INVENTORY_INVALID", "installed_protocols must be an array", 422)
    DeviceDeploymentOrchestrator(get_session()).record_installed_inventory(
        device.id, installed
    )
    supported = body.get("supported_schema_versions", ["1.0"])
    if not isinstance(supported, list) or not all(isinstance(x, str) for x in supported):
        raise EdgeError("PROTOCOL_SCHEMA_SUPPORT_INVALID", "supported schema versions are required", 422)
    try:
        DeviceDeploymentOrchestrator(get_session()).ensure_edge(device.id)
    except DeviceDeploymentError as exc:
        raise EdgeError(str(exc), "protocol dependency cannot be resolved", 409) from exc
    maximum = body.get("max_items", 20)
    if not isinstance(maximum, int) or not 1 <= maximum <= 100:
        raise EdgeError("MAX_ITEMS_INVALID", "max_items must be between 1 and 100", 422)
    deliveries = get_session().scalars(select(EdgeProtocolDelivery).where(
        EdgeProtocolDelivery.edge_device_id == device.id,
        EdgeProtocolDelivery.status.in_(["PENDING", "SENT", "DOWNLOADED"]),
    ).order_by(EdgeProtocolDelivery.id).limit(maximum)).all()
    items = []
    for delivery in deliveries:
        version = get_session().get(ProtocolVersion, delivery.protocol_version_id)
        profile = get_session().get(ProtocolProfile, delivery.protocol_profile_id)
        if (
            version is None or profile is None or version.status != "PUBLISHED"
            or not version.definition_hash or version.signature_algorithm != "Ed25519"
            or not version.signature or not version.signing_key_id
        ):
            delivery.status = "FAILED"
            delivery.error_code = "PROTOCOL_NOT_DISTRIBUTABLE"
            continue
        if str(version.definition_json.get("schema_version")) not in supported:
            delivery.status = "FAILED"
            delivery.error_code = "PROTOCOL_SCHEMA_UNSUPPORTED"
            continue
        items.append(_protocol_package(delivery, version, profile))
        delivery.status = "SENT"
        delivery.attempt_count += 1
        delivery.last_attempt_at = utcnow()
    get_session().add(EdgeAuditLog(
        device_id=device.id, company_id=device.company_id,
        action="edge.protocol.pull", old_values={},
        new_values={"deliveries": len(items)},
        correlation_id=correlation_id(), ip_address=request.remote_addr,
    ))
    get_session().commit()
    return response({"items": items, "distribution_only": True})


@edge_cloud.post("/api/v1/edge/protocols/<protocol_delivery_id>/ack")
def protocol_ack(protocol_delivery_id):
    body = request.get_json(force=True)
    delivery = get_session().scalar(select(EdgeProtocolDelivery).where(
        EdgeProtocolDelivery.delivery_id == protocol_delivery_id
    ))
    if delivery is None:
        raise EdgeError("PROTOCOL_DELIVERY_NOT_FOUND", "protocol delivery not found", 404)
    device = get_session().get(EdgeDevice, delivery.edge_device_id)
    if body.get("edge_device_uuid") != device.device_uuid:
        raise EdgeError("EDGE_IDENTITY_MISMATCH", "wrong Edge identity", 403)
    _require_edge_proof(device, body)
    state = str(body.get("status", ""))
    if state not in {"DOWNLOADED", "VERIFIED", "REJECTED", "FAILED"}:
        raise EdgeError("PROTOCOL_ACK_STATE_INVALID", "invalid protocol acknowledgement", 422)
    version = get_session().get(ProtocolVersion, delivery.protocol_version_id)
    if str(body.get("protocol_version_id")) != str(version.id):
        raise EdgeError("PROTOCOL_VERSION_MISMATCH", "wrong protocol version", 409)
    if state == "VERIFIED" and body.get("definition_hash") != version.definition_hash:
        raise EdgeError("PROTOCOL_HASH_MISMATCH", "verified hash does not match pinned version", 409)
    if delivery.status == state:
        if state == "VERIFIED":
            DeviceDeploymentOrchestrator(get_session()).protocol_verified(delivery)
        get_session().commit()
        return response({"accepted": True, "idempotent": True,
                         "protocol_delivery_id": protocol_delivery_id, "status": state})
    transitions = {
        "PENDING": {"DOWNLOADED", "VERIFIED", "REJECTED", "FAILED"},
        "SENT": {"DOWNLOADED", "VERIFIED", "REJECTED", "FAILED"},
        "DOWNLOADED": {"VERIFIED", "REJECTED", "FAILED"},
        "VERIFIED": {"VERIFIED"},
        "REJECTED": {"REJECTED"},
        "FAILED": {"FAILED"},
    }
    if state not in transitions.get(delivery.status, set()):
        raise EdgeError("PROTOCOL_ACK_STATE_CONFLICT", "invalid protocol state transition", 409)
    delivery.status = state
    delivery.acknowledged_at = utcnow()
    delivery.response_json = {k: v for k, v in body.items() if k != "device_proof"}
    if state == "VERIFIED":
        DeviceDeploymentOrchestrator(get_session()).protocol_verified(delivery)
    else:
        delivery.error_code = str(body.get("error_code") or "")[:100] or None
        delivery.error_message = str(body.get("error_message") or "")[:500] or None
    get_session().add(EdgeAuditLog(
        device_id=device.id, company_id=device.company_id,
        action="edge.protocol.ack", old_values={},
        new_values={"protocol_delivery_id": protocol_delivery_id, "status": state,
                    "protocol_version_id": version.id},
        correlation_id=correlation_id(), ip_address=request.remote_addr,
    ))
    get_session().commit()
    return response({"accepted": True, "idempotent": False,
                     "protocol_delivery_id": protocol_delivery_id, "status": state})


_EDGE_EVENT_TYPES = {
    "SALE", "TRANSACTION", "PAYMENT", "TELEMETRY", "TANK_READING",
    "TANK_TELEMETRY",
    "DEVICE_EVENT", "ALARM", "COMMAND_RESULT", "AUDIT_EVENT",
}


@edge_cloud.post("/api/v1/edge/events/batch")
def edge_events_batch():
    db = get_session()
    body = request.get_json(force=True)
    device = db.scalar(select(EdgeDevice).where(
        EdgeDevice.device_uuid == body.get("edge_device_uuid")
    ))
    if not device:
        raise EdgeError("DEVICE_UNKNOWN", "Edge device not found", 404)
    _require_edge_proof(device, body, db)
    events = body.get("events")
    if not isinstance(events, list) or not 1 <= len(events) <= 100:
        raise EdgeError("EVENT_BATCH_INVALID", "events must contain 1..100 records", 422)
    accepted, duplicates, rejected = [], [], []
    for item in events:
        if not isinstance(item, dict):
            rejected.append({"event_id": None, "reason": "EVENT_SCHEMA_INVALID"})
            continue
        event_id, event_type = item.get("event_id"), item.get("event_type")
        if not isinstance(event_id, str) or not event_id or event_type not in _EDGE_EVENT_TYPES:
            rejected.append({"event_id": event_id, "reason": "EVENT_SCHEMA_INVALID"})
            continue
        payload = item.get("payload")
        if not isinstance(payload, dict) or {"raw_frame", "raw_serial", "shell", "executable"}.intersection(payload):
            rejected.append({"event_id": event_id, "reason": "UNSAFE_EVENT_PAYLOAD"})
            continue
        try:
            occurred = datetime.fromisoformat(str(item["occurred_at"]).replace("Z", "+00:00"))
            sequence = int(item["sequence"])
        except (KeyError, TypeError, ValueError):
            rejected.append({"event_id": event_id, "reason": "EVENT_SCHEMA_INVALID"})
            continue
        # Claim the event before any domain side effect.  A read-before-write
        # check races under concurrent Edge retries; PostgreSQL's unique
        # constraint is the authoritative idempotency boundary instead.
        claimed_id = db.scalar(
            pg_insert(EdgeIngestedEvent)
            .values(
                edge_device_id=device.id, event_id=event_id,
                event_type=event_type, station_id=device.station_id,
                device_id=str(item.get("device_id") or "") or None,
                occurred_at=occurred, sequence=sequence,
                priority=str(item.get("priority") or "NORMAL"),
                payload_json=payload,
            )
            .on_conflict_do_nothing(constraint="uq_edge_ingested_event")
            .returning(EdgeIngestedEvent.id)
        )
        if claimed_id is None:
            duplicates.append(event_id)
            continue
        if event_type in {"SALE", "TRANSACTION"}:
            try:
                transaction_id = str(payload["transaction_id"])
                ended_at = datetime.fromisoformat(str(payload["ended_at"]).replace("Z", "+00:00"))
                started_at = datetime.fromisoformat(str(payload["started_at"]).replace("Z", "+00:00"))
                if ended_at.tzinfo is None:
                    ended_at = ended_at.replace(tzinfo=ZoneInfo("Asia/Riyadh"))
                if started_at.tzinfo is None:
                    started_at = started_at.replace(tzinfo=ZoneInfo("Asia/Riyadh"))
                liters = float(payload["liters"])
                if liters <= 0:
                    raise ValueError("INVALID_LITERS")
                bus = db.scalar(select(CloudBusDevice).where(
                    CloudBusDevice.cloud_device_id == str(payload["cloud_device_id"]),
                    CloudBusDevice.edge_device_id == device.id,
                    CloudBusDevice.device_type == "FUEL_PUMP",
                    CloudBusDevice.status.notin_(
                        ["DECOMMISSIONED", "SUPERSEDED", "DELETED"]
                    ),
                ))
                config = db.get(
                    DeviceConfigurationVersion,
                    bus.last_configuration_version_id if bus else None,
                )
                definition = (
                    (config.configuration_json or {}).get("configuration") or {}
                    if config else {}
                )
                pump = db.get(Pump, int(definition.get("pump_id") or 0))
                nozzle = db.scalar(select(Nozzle).where(
                    Nozzle.station_id == device.station_id,
                    Nozzle.nozzle_id == str(payload["nozzle_id"]),
                    Nozzle.pump_id == (pump.id if pump else -1),
                    Nozzle.deleted_at.is_(None),
                ))
                address = str(payload.get("device_address") or "").removeprefix("0x").upper()
                configured_nozzle = next((
                    item for item in (bus.protocol_config_json or {}).get("nozzles", [])
                    if str(item.get("id")) == str(payload["nozzle_id"])
                ), None) if bus else None
                configured_address = str(
                    (configured_nozzle or {}).get("address") or ""
                ).removeprefix("0x").upper()
                if (
                    not pump or not nozzle or nozzle.pump_id != pump.id
                    or not address or address != configured_address
                ):
                    raise ValueError("PUMP_NOZZLE_IDENTITY_UNKNOWN")
                sale = db.scalar(select(SaleTransaction).where(
                    SaleTransaction.station_id == device.station_id,
                    SaleTransaction.transaction_key == transaction_id,
                ))
                if sale is None:
                    # Sales are operational facts and must never be discarded
                    # merely because nobody opened the Operations page.  Bring
                    # the effective station schedule into a durable
                    # ShiftSession before inserting. Delayed Edge outbox
                    # replay must reuse the historical shift and must never
                    # rewind or close the station's currently active shift.
                    station = db.get(Station, device.station_id)
                    if station is None:
                        raise ValueError("STATION_UNKNOWN")
                    shift = db.scalar(select(ShiftSession).where(
                        ShiftSession.station_id == device.station_id,
                        ShiftSession.actual_started_at <= ended_at,
                        (
                            ShiftSession.actual_closed_at.is_(None)
                            | (ShiftSession.actual_closed_at >= ended_at)
                        ),
                    ).order_by(ShiftSession.actual_started_at.desc()))
                    from app.operations.routes import (
                        _load_plan, _parse_utc, _runtime_window,
                        _sync_shift_runtime,
                    )
                    shift_plan = _load_plan(db, station.id)[1]
                    if shift is None and ended_at < utcnow() - timedelta(minutes=5):
                        historical_window = _runtime_window(shift_plan, ended_at)
                        if historical_window is not None:
                            shift = ShiftSession(
                                company_id=station.company_id,
                                station_id=station.id,
                                shift_slot=historical_window["slot"],
                                shift_label=historical_window["label"],
                                mode=shift_plan["mode"],
                                planned_start_time=historical_window["start"],
                                planned_end_time=historical_window["end"],
                                actual_started_at=_parse_utc(
                                    historical_window["planned_start_at"]
                                ),
                                actual_closed_at=_parse_utc(
                                    historical_window["planned_end_at"]
                                ),
                                status="closed",
                                opened_by="system",
                                closed_by="system",
                                notes="Created for delayed Edge sales replay",
                                metadata_json={
                                    "schedule_key": historical_window["schedule_key"],
                                    "schedule_date": historical_window["schedule_date"],
                                    "planned_start_at": historical_window["planned_start_at"],
                                    "planned_end_at": historical_window["planned_end_at"],
                                    "late_edge_replay": True,
                                },
                            )
                        else:
                            shift = ShiftSession(
                                company_id=station.company_id,
                                station_id=station.id,
                                shift_slot="AFTER_HOURS",
                                shift_label="وردية تلقائية خارج الجدول",
                                mode=shift_plan["mode"],
                                planned_start_time=started_at.astimezone(
                                    ZoneInfo("Asia/Riyadh")
                                ).strftime("%H:%M"),
                                planned_end_time=ended_at.astimezone(
                                    ZoneInfo("Asia/Riyadh")
                                ).strftime("%H:%M"),
                                actual_started_at=started_at,
                                actual_closed_at=ended_at,
                                status="closed",
                                opened_by="system",
                                closed_by="system",
                                notes="Created for delayed after-hours Edge sale",
                                metadata_json={"late_edge_replay": True, "after_hours": True},
                            )
                        db.add(shift)
                        db.flush()
                    elif shift is None:
                        shift, current_window = _sync_shift_runtime(
                            db, station, shift_plan, now=ended_at
                        )
                        if shift is None and current_window is None:
                            shift = ShiftSession(
                                company_id=station.company_id,
                                station_id=station.id,
                                shift_slot="AFTER_HOURS",
                                shift_label="وردية تلقائية خارج الجدول",
                                mode=shift_plan["mode"],
                                planned_start_time=ended_at.astimezone(
                                    ZoneInfo("Asia/Riyadh")
                                ).strftime("%H:%M"),
                                planned_end_time="—",
                                actual_started_at=ended_at,
                                status="active",
                                opened_by="system",
                                notes="Auto-opened to preserve Edge sales outside configured windows",
                                metadata_json={
                                    "schedule_key": (
                                        "after-hours:"
                                        + ended_at.astimezone(
                                            ZoneInfo("Asia/Riyadh")
                                        ).date().isoformat()
                                    ),
                                    "after_hours": True,
                                    "auto_synced_at": utcnow().isoformat(),
                                },
                            )
                            db.add(shift)
                            db.flush()
                    if shift is None:
                        raise ValueError("SHIFT_HISTORY_NOT_FOUND")
                    sale = SaleTransaction(
                        company_id=device.company_id, station_id=device.station_id,
                        shift_id=shift.id if shift else None,
                        transaction_key=transaction_id, pump_id=pump.id, nozzle_id=nozzle.id,
                        pump_number=pump.pump_number, nozzle_number=nozzle.nozzle_number,
                        fuel_code=str(payload["fuel_code"]),
                        fuel_name_ar=str(payload.get("fuel_name") or payload["fuel_code"]),
                        liters=liters, unit_price=float(payload.get("unit_price") or 0),
                        amount=float(payload.get("amount") or 0), status="completed",
                        started_at=started_at, ended_at=ended_at,
                        source="edge_runtime", raw_json={},
                    )
                    db.add(sale); db.flush()
                    customer_session = db.scalar(select(FuelingSession).where(
                        FuelingSession.station_id == station.id,
                        FuelingSession.pump_id == pump.id,
                        FuelingSession.nozzle_id == nozzle.id,
                        FuelingSession.status.in_(["PUMP_AUTHORIZED", "READY_TO_FUEL", "FUELING", "COMPLETED", "SETTLEMENT_PENDING"]),
                        FuelingSession.created_at <= ended_at,
                    ).order_by(FuelingSession.created_at.desc()).with_for_update())
                    if customer_session is not None:
                        hold = db.get(WalletHold, customer_session.hold_id)
                        wallet = db.scalar(select(CustomerWallet).where(
                            CustomerWallet.id == customer_session.wallet_id).with_for_update())
                        actual = Decimal(str(payload.get("amount") or 0)).quantize(Decimal("0.01"))
                        held = Decimal(str(hold.amount)) if hold else Decimal("0")
                        if not hold or hold.status != "HELD" or wallet is None or actual < 0 or actual > held:
                            customer_session.status = "SETTLEMENT_REVIEW"
                            customer_session.failure_code = "FINAL_SALE_HOLD_MISMATCH"
                        else:
                            before_available = Decimal(str(wallet.balance)) - Decimal(str(wallet.reserved_balance))
                            wallet.balance = Decimal(str(wallet.balance)) - actual
                            wallet.reserved_balance = max(Decimal("0"), Decimal(str(wallet.reserved_balance)) - held)
                            wallet.version += 1
                            hold.captured_amount = actual; hold.status = "CAPTURED"; hold.released_at = utcnow()
                            db.add(WalletTransaction(company_id=station.company_id, wallet_id=wallet.id,
                                transaction_type="FUELING_CAPTURE", amount=-actual,
                                balance_before=before_available, balance_after=before_available,
                                reference=f"capture:{customer_session.public_id}", idempotency_key=f"capture:{customer_session.public_id}",
                                metadata_json={"hold_id": hold.public_id, "sale_id": sale.id}))
                            released = held - actual
                            if released > 0:
                                db.add(WalletTransaction(company_id=station.company_id, wallet_id=wallet.id,
                                    transaction_type="HOLD_RELEASE", amount=released,
                                    balance_before=before_available, balance_after=before_available + released,
                                    reference=f"release:{customer_session.public_id}", idempotency_key=f"release:{customer_session.public_id}",
                                    metadata_json={"hold_id": hold.public_id, "sale_id": sale.id}))
                            customer_session.status = "SETTLED"; customer_session.settled_at = utcnow()
                        customer_session.transaction_id = sale.id
                        customer_session.actual_amount = actual
                        customer_session.actual_liters = Decimal(str(liters))
                        customer_session.unit_price = Decimal(str(payload.get("unit_price") or 0))
                        customer_session.fuel_code = str(payload["fuel_code"])
                        customer_session.completed_at = ended_at
                        customer_session.event_version += 1
                        sale.customer_id = customer_session.customer_id
                        sale.fueling_session_id = customer_session.id
                        get_session().add(CustomerRealtimeEvent(customer_id=customer_session.customer_id,
                            event_type="FUELING_SESSION_UPDATED", entity_id=customer_session.public_id,
                            event_version=customer_session.event_version,
                            payload_json={"sessionId": customer_session.public_id, "status": customer_session.status,
                                "actualAmount": float(actual), "actualLiters": liters}))
                        get_session().add(CustomerAuditEvent(customer_id=customer_session.customer_id,
                            company_id=customer_session.company_id, station_id=customer_session.station_id,
                            fueling_session_id=customer_session.id, correlation_id=str(uuid4()),
                            action="FUELING_SETTLED" if customer_session.status == "SETTLED" else "FUELING_SETTLEMENT_REVIEW",
                            entity_type="fueling_session", entity_id=customer_session.public_id,
                            details_json={"sale_id": sale.id, "actual_amount": str(actual)}, source="EDGE"))
                    if shift:
                        shift.sales_count += 1
                        shift.sales_liters = float(shift.sales_liters or 0) + liters
                        shift.sales_amount = (
                            float(shift.sales_amount or 0)
                            + float(payload.get("amount") or 0)
                        )
                from app.calibration.production import pipeline
                try:
                    pipeline.attribution.on_sale_completed(db, sale)
                except ValueError as calibration_error:
                    # Fuel-line/nozzle mapping gates calibration evidence, not
                    # financial sale durability.  Keep the immutable sale and
                    # expose the explicit attribution state for later repair.
                    sale.raw_json = {
                        **(sale.raw_json or {}),
                        "calibration_attribution": str(calibration_error),
                    }
            except (KeyError, TypeError, ValueError) as exc:
                rejected.append({"event_id": event_id, "reason": str(exc)})
                continue
        if event_type == "TANK_TELEMETRY":
            bus_device = db.scalar(select(CloudBusDevice).where(
                CloudBusDevice.cloud_device_id == str(item.get("device_id") or ""),
                CloudBusDevice.edge_device_id == device.id,
            ))
            tank = db.scalar(select(Tank).where(
                Tank.cloud_bus_device_id == bus_device.id,
                Tank.deleted_at.is_(None),
            )) if bus_device else None
            if tank:
                reading = {
                    "fuel_level_mm": payload.get("level_mm"),
                    "water_level_mm": payload.get("water_mm"),
                    "temperature_c": payload.get("temperature_c"),
                    "probe_status": payload.get("probe_status") or "MEASUREMENT_RECEIVED",
                    "last_seen_at": payload.get("read_at") or occurred.isoformat(),
                    "protocol_version": payload.get("protocol_version"),
                    "volume_liters": payload.get("volume_liters"),
                    "fill_percent": payload.get("fill_percent"),
                    "volume_confidence": payload.get("volume_confidence"),
                    "calibration_profile_version": payload.get("calibration_profile_version"),
                    "calibration_status": (
                        payload.get("calibration_status")
                        or ("CALIBRATION_REQUIRED" if not tank.calibration_profile_id else "CALIBRATED")
                    ),
                }
                db.add(DeviceReadingSnapshot(
                    station_id=tank.station_id, entity_type="tank",
                    unified_entity_id=tank.id, source="nnexoris_edge_control_plane",
                    reading_json=reading, captured_at=occurred,
                ))
                db.add(CalibrationInternalEvent(
                    event_id=str(uuid4()), event_type="CALIBRATION_TANK_TELEMETRY",
                    tank_id=tank.id,
                    payload_json={"edge_event_id": event_id, "captured_at": occurred.isoformat()},
                ))
                probe = db.scalar(select(Probe).where(
                    Probe.tank_id == tank.id, Probe.deleted_at.is_(None)
                ))
                if probe:
                    probe.last_seen_at = occurred
                    probe.status = reading["probe_status"]
                tank.status = "ACTIVE"
        accepted.append(event_id)
    db.add(EdgeAuditLog(
        device_id=device.id, company_id=device.company_id,
        action="edge.events.batch", old_values={},
        new_values={"accepted": len(accepted), "duplicates": len(duplicates), "rejected": len(rejected)},
        correlation_id=correlation_id(), ip_address=request.remote_addr,
    ))
    db.commit()
    return response({"accepted_event_ids": accepted,
                     "duplicate_event_ids": duplicates,
                     "rejected_events": rejected})


@edge_cloud.post("/api/v1/edge/calibrations/pull")
def calibration_pull():
    body = request.get_json(force=True)
    db = get_session()
    device = db.scalar(select(EdgeDevice).where(
        EdgeDevice.device_uuid == body.get("edge_device_uuid")
    ))
    if not device:
        raise EdgeError("DEVICE_UNKNOWN", "Edge device not found", 404)
    _require_edge_proof(device, body)
    rows = db.scalars(select(CalibrationDelivery).where(
        CalibrationDelivery.edge_device_id == device.id,
        CalibrationDelivery.status.in_(("PENDING", "DELIVERED")),
    ).order_by(CalibrationDelivery.id).limit(20)).all()
    items = []
    for delivery in rows:
        package = db.get(CalibrationPackageVersion, delivery.package_version_id)
        delivery.status, delivery.delivered_at = "DELIVERED", utcnow()
        delivery.attempts += 1
        items.append({
            "delivery_id": delivery.delivery_id,
            "package_id": package.package_id,
            "envelope": package.envelope_json,
            "payload_hash": package.payload_hash,
            "signature": package.signature,
            "signature_algorithm": package.signature_algorithm,
            "signing_key_id": package.signing_key_id,
        })
    db.commit()
    return response({"items": items})


@edge_cloud.post("/api/v1/edge/calibrations/<string:delivery_id>/ack")
def calibration_ack(delivery_id):
    body = request.get_json(force=True)
    db = get_session()
    device = db.scalar(select(EdgeDevice).where(
        EdgeDevice.device_uuid == body.get("edge_device_uuid")
    ))
    if not device:
        raise EdgeError("DEVICE_UNKNOWN", "Edge device not found", 404)
    _require_edge_proof(device, body)
    delivery = db.scalar(select(CalibrationDelivery).where(
        CalibrationDelivery.delivery_id == delivery_id,
        CalibrationDelivery.edge_device_id == device.id,
    ))
    if not delivery:
        raise EdgeError("CALIBRATION_DELIVERY_UNKNOWN", "delivery not found", 404)
    state = str(body.get("status") or "")
    if state not in {"VERIFIED", "ACTIVE", "REJECTED", "FAILED"}:
        raise EdgeError("CALIBRATION_ACK_INVALID", "invalid calibration state", 422)
    if delivery.status == state:
        return response({"accepted": True, "idempotent": True, "status": state})
    delivery.status, delivery.acknowledged_at = state, utcnow()
    delivery.response_json = {k: v for k, v in body.items() if k != "device_proof"}
    delivery.error_code = str(body.get("error_code") or "")[:100] or None
    delivery.error_message = str(body.get("error_message") or "")[:500] or None
    db.commit()
    return response({"accepted": True, "idempotent": False, "status": state})


@edge_cloud.post("/api/v1/edge/configurations/pull")
def configuration_pull():
    body = request.get_json(force=True); db = get_session()
    device = db.scalar(select(EdgeDevice).where(EdgeDevice.device_uuid == body.get("edge_device_uuid")))
    if not device: raise EdgeError("DEVICE_UNKNOWN", "Edge device not found", 404)
    _require_edge_proof(device, body)
    if db.get_bind().dialect.name == "postgresql":
        # Serialize materialization per Edge. Multiple workers/pull retries must
        # never acquire CloudBusDevice rows in conflicting transactions.
        db.execute(select(func.pg_advisory_xact_lock(0x4E585300 + device.id)))
    DesiredStateMaterializationService(
        db, _contract_signer()
    ).reconcile_edge(device.id, reason="CONFIGURATION_PULL_RECONCILIATION")
    db.flush()
    rows = db.scalars(select(EdgeConfigurationDelivery).where(EdgeConfigurationDelivery.edge_device_id == device.id, EdgeConfigurationDelivery.status.in_(["PENDING", "SENT"])).order_by(EdgeConfigurationDelivery.id).limit(50)).all()
    items = []
    for delivery in rows:
        version = db.get(DeviceConfigurationVersion, delivery.configuration_version_id)
        if not version or version.signature_algorithm != "Ed25519" or not version.signing_key_id:
            delivery.status, delivery.error_code, delivery.error_message = "FAILED", "LEGACY_SIGNATURE_BLOCKED", "unsigned or legacy configuration requires re-signing"
            version.status, version.failure_code, version.failure_message = "FAILED", "LEGACY_SIGNATURE_BLOCKED", "Ed25519 signature required"
            continue
        envelope = version.configuration_json
        try:
            expires_at = datetime.fromisoformat(
                str(envelope["expires_at"]).replace("Z", "+00:00")
            )
        except (KeyError, TypeError, ValueError):
            delivery.status, delivery.error_code = "FAILED", "DELIVERY_EXPIRY_INVALID"
            version.status, version.failure_code = "FAILED", "DELIVERY_EXPIRY_INVALID"
            continue
        if expires_at <= utcnow():
            delivery.status, delivery.error_code = "EXPIRED", "DELIVERY_EXPIRED"
            version.status, version.failure_code = "EXPIRED", "DELIVERY_EXPIRED"
            continue
        delivery.status, delivery.attempt_count, delivery.last_attempt_at = "SENT", delivery.attempt_count + 1, utcnow(); version.delivery_status, version.delivered_at = "SENT", utcnow()
        items.append({"delivery_id": delivery.delivery_id, "configuration_version_id": version.id,
            "edge_device_uuid": device.device_uuid, "envelope": envelope,
            "configuration_hash": version.configuration_hash, "signature": version.signature,
            "signature_algorithm": version.signature_algorithm, "signing_key_id": version.signing_key_id,
            "issued_at": envelope["issued_at"], "expires_at": envelope["expires_at"]})
    db.commit(); return response({"items": items, "stage_only": True})


@edge_cloud.post("/api/v1/edge/configurations/<delivery_id>/ack")
def configuration_ack(delivery_id):
    body = request.get_json(force=True); delivery = get_session().scalar(select(EdgeConfigurationDelivery).where(EdgeConfigurationDelivery.delivery_id == delivery_id));
    if not delivery: raise EdgeError("DELIVERY_NOT_FOUND", "configuration delivery not found", 404)
    device = get_session().get(EdgeDevice, delivery.edge_device_id)
    if body.get("edge_device_uuid") != device.device_uuid: raise EdgeError("EDGE_IDENTITY_MISMATCH", "wrong Edge identity", 403)
    _require_edge_proof(device, body)
    state = str(body.get("status", ""));
    if state not in {"VALIDATED", "STAGED", "FAILED", "REJECTED", "EXPIRED"}: raise EdgeError("CONFIGURATION_STATE_INVALID", "ACTIVE is not allowed in this phase", 422)
    transitions = {"PENDING": {"VALIDATED", "FAILED", "REJECTED", "EXPIRED"}, "SENT": {"VALIDATED", "FAILED", "REJECTED", "EXPIRED"}, "VALIDATED": {"VALIDATED", "STAGED"}, "STAGED": {"STAGED"}, "FAILED": {"FAILED"}, "REJECTED": {"REJECTED"}, "EXPIRED": {"EXPIRED"}}
    if state not in transitions.get(delivery.status, set()): raise EdgeError("CONFIGURATION_STATE_CONFLICT", "invalid configuration state transition", 409)
    version = get_session().get(DeviceConfigurationVersion, delivery.configuration_version_id); delivery.status = state; delivery.acknowledged_at = utcnow(); delivery.response_json = {k: v for k, v in body.items() if k != "device_proof"}
    if str(body.get("configuration_version_id")) != str(version.id):
        raise EdgeError("CONFIGURATION_VERSION_MISMATCH", "wrong configuration version", 409)
    if state == "VALIDATED": version.status, version.validated_at = "VALIDATED", utcnow()
    elif state == "STAGED": version.status, version.staged_at = "STAGED", utcnow()
    elif state == "FAILED": version.status, version.failed_at, version.failure_code, version.failure_message = "FAILED", utcnow(), body.get("error_code"), str(body.get("error_message", ""))[:500]
    elif state in {"REJECTED", "EXPIRED"}: version.status = state
    get_session().add(EdgeAuditLog(device_id=device.id, company_id=device.company_id,
        action="edge.configuration.ack", old_values={},
        new_values={"delivery_id": delivery_id, "configuration_version_id": version.id,
                    "status": state}, correlation_id=correlation_id(),
        ip_address=request.remote_addr))
    bus = get_session().get(CloudBusDevice, version.device_id)
    if bus and version.device_category != bus.device_type:
        bus = None
    if bus:
        DeviceDeploymentReconciliationService(get_session()).reconcile_device(
            bus.id, source="EDGE_CONFIGURATION_ACK"
        )
        if bus.configuration_status == "STAGED":
            waiting = get_session().scalars(select(
                HardwareActivationDelivery
            ).where(
                HardwareActivationDelivery.device_id == bus.id,
                HardwareActivationDelivery.action == "ACTIVATE_DEVICE_RUNTIME",
                HardwareActivationDelivery.status == "WAITING_FOR_CONFIGURATION",
            )).all()
            for activation in waiting:
                if not _is_expired(activation.expires_at):
                    activation.status = "PENDING"
                    bus.activation_status = "ACTIVATION_QUEUED"
                    bus.activation_blocked_reason = None
                else:
                    activation.status = "EXPIRED"
    get_session().commit(); return response({"accepted": True, "delivery_id": delivery_id, "status": state})


@edge_cloud.post("/api/v1/edge-devices/<int:device_id>/contracts")
@require_permission("edge.manage")
def create_edge_contract(device_id):
    device = device_for_user(device_id)
    body = request.get_json(force=True)
    required_lists = (
        "allowed_device_types",
        "allowed_ports",
        "allowed_protocols",
        "allowed_command_classes",
    )
    if any(
        not isinstance(body.get(name), list) or not body[name]
        for name in required_lists
    ):
        raise EdgeError("CONTRACT_POLICY_INVALID", "contract allowlists are required", 422)
    if any(not str(value).startswith("by-id:") for value in body["allowed_ports"]):
        raise EdgeError("CONTRACT_PORT_IDENTITY_INVALID", "stable by-id identities are required", 422)
    activation_policy = str(
        body.get("hardware_activation_policy", "AUTOMATIC_DESIRED_STATE")
    )
    if activation_policy not in {"AUTOMATIC_DESIRED_STATE", "MANUAL_ONLY", "DISABLED"}:
        raise EdgeError("CONTRACT_ACTIVATION_POLICY_INVALID", "invalid activation policy", 422)
    definition = {
        "company_id": int(body["company_id"]),
        "station_id": int(body["station_id"]),
        "hardware_policy": {
            "allowed_device_types": list(body["allowed_device_types"]),
            "activation_policy": activation_policy,
        },
        "port_policy": {
            "mode": "SELECTED_PORTS_ONLY",
            "ports": [
                {
                    "stable_identity": stable_identity,
                    "allowed_device_types": list(body["allowed_device_types"]),
                }
                for stable_identity in body["allowed_ports"]
            ],
        },
        "protocol_policy": {
            "mode": "SELECTED_PROTOCOLS_ONLY",
            "protocol_codes": list(body["allowed_protocols"]),
        },
        "command_policy": {
            "allowed_command_classes": list(body["allowed_command_classes"])
        },
        "offline_policy": {
            "allow_offline_operation": bool(body.get("allow_offline_operation", True))
        },
        "persistent_autostart_policy": {
            "allow_persistent_autostart": bool(
                body.get("allow_persistent_autostart", True)
            )
        },
        "sync_policy": body.get(
            "sync_policy",
            {
                "telemetry_sync_enabled": True,
                "sales_sync_enabled": True,
                "audit_sync_enabled": True,
                "batch_size": 100,
            },
        ),
        "expires_at": body.get("expires_at"),
    }
    try:
        contract, version, delivery = EdgeContractService(
            get_session(), _contract_signer()
        ).create(device, definition, session.get("unified_user_id"))
    except (ContractControlError, ConfigurationSigningError, KeyError, ValueError) as exc:
        get_session().rollback()
        raise EdgeError(str(exc), "contract could not be created", 409) from exc
    get_session().add(
        EdgeAuditLog(
            device_id=device.id,
            company_id=device.company_id,
            user_id=session.get("unified_user_id"),
            action="EDGE_CONTRACT_SIGNED",
            old_values={},
            new_values={
                "contract_code": contract.contract_code,
                "version": version.version_number,
                "delivery_id": delivery.delivery_id,
            },
            correlation_id=correlation_id(),
            ip_address=request.remote_addr,
        )
    )
    get_session().commit()
    return response(
        {
            "contract_id": contract.id,
            "contract_code": contract.contract_code,
            "contract_version_id": version.id,
            "version": version.version_number,
            "definition_hash": version.definition_hash,
            "signature_algorithm": version.signature_algorithm,
            "signing_key_id": version.signing_key_id,
            "delivery_id": delivery.delivery_id,
            "status": delivery.status,
        },
        201,
    )


@edge_cloud.post("/api/v1/edge-devices/<int:device_id>/contracts/versions")
@require_permission("edge.manage")
def revise_edge_contract(device_id):
    device = device_for_user(device_id)
    body = request.get_json(force=True)
    required_lists = (
        "allowed_device_types", "allowed_ports",
        "allowed_protocols", "allowed_command_classes",
    )
    if any(not isinstance(body.get(name), list) or not body[name] for name in required_lists):
        raise EdgeError("CONTRACT_POLICY_INVALID", "contract allowlists are required", 422)
    available_ports = set(get_session().scalars(select(EdgeSerialPort.stable_identity).where(
        EdgeSerialPort.edge_device_id == device.id
    )).all())
    if not set(map(str, body["allowed_ports"])).issubset(available_ports):
        raise EdgeError("CONTRACT_PORT_NOT_OWNED_BY_EDGE", "port does not belong to this Edge", 422)
    allowed_types = {
        "TANK_GAUGE", "FUEL_PUMP", "PRICE_BOARD", "RFID_READER",
        "PAYMENT_TERMINAL", "SENSOR", "CONTROLLER",
    }
    if not set(map(str, body["allowed_device_types"])).issubset(allowed_types):
        raise EdgeError("CONTRACT_DEVICE_TYPE_INVALID", "unsupported device type", 422)
    activation_policy = str(
        body.get("hardware_activation_policy", "AUTOMATIC_DESIRED_STATE")
    )
    if activation_policy not in {"AUTOMATIC_DESIRED_STATE", "MANUAL_ONLY", "DISABLED"}:
        raise EdgeError("CONTRACT_ACTIVATION_POLICY_INVALID", "invalid activation policy", 422)
    definition = {
        "company_id": device.company_id,
        "station_id": device.station_id,
        "hardware_policy": {
            "allowed_device_types": list(dict.fromkeys(body["allowed_device_types"])),
            "activation_policy": activation_policy,
        },
        "port_policy": {
            "mode": "SELECTED_PORTS_ONLY",
            "ports": [{"stable_identity": value,
                       "allowed_device_types": list(dict.fromkeys(body["allowed_device_types"]))}
                      for value in dict.fromkeys(body["allowed_ports"])],
        },
        "protocol_policy": {
            "mode": "SELECTED_PROTOCOLS_ONLY",
            "protocol_codes": list(dict.fromkeys(body["allowed_protocols"])),
        },
        "command_policy": {
            "allowed_command_classes": list(dict.fromkeys(body["allowed_command_classes"]))
        },
        "offline_policy": {
            "allow_offline_operation": bool(body.get("allow_offline_operation"))
        },
        "persistent_autostart_policy": {
            "allow_persistent_autostart": bool(body.get("allow_persistent_autostart"))
        },
        "sync_policy": body.get("sync_policy") or {
            "telemetry_sync_enabled": True, "sales_sync_enabled": True,
            "audit_sync_enabled": True, "batch_size": 100,
        },
        "expires_at": body.get("expires_at"),
    }
    try:
        contract, version, delivery = EdgeContractService(
            get_session(), _contract_signer()
        ).revise(device, definition, session.get("unified_user_id"))
    except (ContractControlError, ConfigurationSigningError, KeyError, ValueError) as exc:
        get_session().rollback()
        raise EdgeError(str(exc), "contract revision could not be created", 409) from exc
    get_session().add(EdgeAuditLog(
        device_id=device.id, company_id=device.company_id,
        user_id=session.get("unified_user_id"), action="EDGE_CONTRACT_REVISED",
        old_values={"current_version_id": contract.current_version_id},
        new_values={"contract_code": contract.contract_code,
                    "version": version.version_number,
                    "delivery_id": delivery.delivery_id},
        correlation_id=correlation_id(), ip_address=request.remote_addr,
    ))
    get_session().commit()
    return response({
        "contract_id": contract.id, "contract_code": contract.contract_code,
        "contract_version_id": version.id, "version": version.version_number,
        "definition_hash": version.definition_hash, "delivery_id": delivery.delivery_id,
        "status": delivery.status,
    }, 201)


@edge_cloud.post("/api/v1/edge-devices/<int:device_id>/contracts/versions/<int:version_id>/approve")
@require_permission("edge.manage")
def approve_edge_contract_version(device_id, version_id):
    if normalize_role(session.get("unified_role")) != "Super Admin":
        raise EdgeError(
            "SUPER_ADMIN_APPROVAL_REQUIRED",
            "only a Super Admin can approve an Edge contract",
            403,
        )
    device = device_for_user(device_id)
    db = get_session()
    contract = db.scalar(select(EdgeContract).where(
        EdgeContract.edge_device_id == device.id
    ))
    version = db.get(EdgeContractVersion, version_id)
    delivery = db.scalar(select(EdgeContractDelivery).where(
        EdgeContractDelivery.contract_version_id == version_id,
        EdgeContractDelivery.edge_device_id == device.id,
    ))
    if not contract or not version or version.contract_id != contract.id or not delivery:
        raise EdgeError("CONTRACT_VERSION_UNKNOWN", "contract version not found", 404)
    if version.status == "ACTIVE":
        return response({"approved": True, "idempotent": True, "status": "ACTIVE"})
    if version.status != "PENDING_APPROVAL" or delivery.status != "WAITING_APPROVAL":
        raise EdgeError("CONTRACT_APPROVAL_STATE_CONFLICT", "version is not waiting approval", 409)
    version.status = "QUEUED"
    delivery.status = "PENDING"
    if contract.current_version_id is None:
        contract.status = "SIGNED"
    db.add(EdgeAuditLog(
        device_id=device.id, company_id=device.company_id,
        user_id=session.get("unified_user_id"), action="EDGE_CONTRACT_APPROVED",
        old_values={"version_status": "PENDING_APPROVAL", "delivery_status": "WAITING_APPROVAL"},
        new_values={"version": version.version_number, "version_status": "QUEUED",
                    "delivery_id": delivery.delivery_id, "delivery_status": "PENDING",
                    "approved_by_role": "Super Admin"},
        correlation_id=correlation_id(), ip_address=request.remote_addr,
    ))
    db.commit()
    return response({
        "approved": True, "idempotent": False, "contract_code": contract.contract_code,
        "version": version.version_number, "delivery_id": delivery.delivery_id,
        "status": delivery.status,
    })


@edge_cloud.post("/api/v1/edge/contracts/pull")
def contract_pull():
    body = request.get_json(force=True)
    device = get_session().scalar(
        select(EdgeDevice).where(
            EdgeDevice.device_uuid == body.get("edge_device_uuid")
        )
    )
    if not device:
        raise EdgeError("DEVICE_UNKNOWN", "Edge device not found", 404)
    _require_edge_proof(device, body)
    rows = get_session().scalars(
        select(EdgeContractDelivery)
        .where(
            EdgeContractDelivery.edge_device_id == device.id,
            EdgeContractDelivery.status.in_(["PENDING", "DELIVERED", "DOWNLOADED"]),
        )
        .order_by(EdgeContractDelivery.id)
        .limit(10)
    ).all()
    items = []
    for delivery in rows:
        version = get_session().get(
            EdgeContractVersion, delivery.contract_version_id
        )
        contract = get_session().get(EdgeContract, delivery.contract_id)
        if (
            _is_expired(delivery.expires_at)
            or version.status in {"REVOKED", "EXPIRED", "FAILED"}
        ):
            delivery.status = "EXPIRED"
            continue
        items.append(
            {
                "delivery_id": delivery.delivery_id,
                "contract_id": contract.id,
                "contract_version_id": version.id,
                "definition_json": version.definition_json,
                "definition_hash": version.definition_hash,
                "envelope": version.signed_envelope_json,
                "signature": version.signature,
                "signature_algorithm": version.signature_algorithm,
                "signing_key_id": version.signing_key_id,
            }
        )
        delivery.status = "DELIVERED"
        delivery.attempt_count += 1
        delivery.last_attempt_at = utcnow()
    get_session().commit()
    return response({"items": items})


@edge_cloud.post("/api/v1/edge/contracts/fallback-approve")
def contract_fallback_approve():
    body = request.get_json(force=True)
    db = get_session()
    device = db.scalar(select(EdgeDevice).where(
        EdgeDevice.device_uuid == body.get("edge_device_uuid")
    ))
    if not device:
        raise EdgeError("DEVICE_UNKNOWN", "Edge device not found", 404)
    _require_edge_proof(device, body)
    contract = db.scalar(select(EdgeContract).where(
        EdgeContract.edge_device_id == device.id,
        EdgeContract.status == "ACTIVE",
    ))
    if not contract or not contract.current_version_id:
        return response({"approved": False, "reason": "ACTIVE_CONTRACT_REQUIRED"})
    delivery = db.scalar(select(EdgeContractDelivery).where(
        EdgeContractDelivery.contract_id == contract.id,
        EdgeContractDelivery.status == "WAITING_APPROVAL",
    ).order_by(EdgeContractDelivery.id))
    if not delivery:
        return response({"approved": False, "reason": "NO_WAITING_REVISION"})
    grace_hours = max(1, int(os.getenv("PETROB_EDGE_CONTRACT_FALLBACK_APPROVAL_HOURS", "24")))
    eligible_at = delivery.created_at + timedelta(hours=grace_hours)
    if utcnow() < eligible_at:
        return response({
            "approved": False, "reason": "SUPER_ADMIN_GRACE_PERIOD",
            "eligible_at": eligible_at.isoformat(),
        })
    active = db.get(EdgeContractVersion, contract.current_version_id)
    proposed = db.get(EdgeContractVersion, delivery.contract_version_id)
    if not active or not proposed or not is_non_expanding_revision(
        active.definition_json, proposed.definition_json
    ):
        return response({
            "approved": False, "reason": "SUPER_ADMIN_REQUIRED_FOR_PERMISSION_EXPANSION",
        })
    proposed.status = "QUEUED"
    delivery.status = "PENDING"
    db.add(EdgeAuditLog(
        device_id=device.id, company_id=device.company_id,
        action="EDGE_CONTRACT_FALLBACK_APPROVED",
        old_values={"version_status": "PENDING_APPROVAL", "delivery_status": "WAITING_APPROVAL"},
        new_values={"version": proposed.version_number, "version_status": "QUEUED",
                    "delivery_id": delivery.delivery_id, "delivery_status": "PENDING",
                    "approval_actor": "EDGE_DEVICE_PROOF",
                    "policy": "NON_EXPANDING_AFTER_GRACE",
                    "grace_hours": grace_hours},
        correlation_id=correlation_id(), ip_address=request.remote_addr,
    ))
    db.commit()
    return response({
        "approved": True, "reason": "NON_EXPANDING_EDGE_FALLBACK",
        "delivery_id": delivery.delivery_id, "version": proposed.version_number,
    })


@edge_cloud.post("/api/v1/edge/contracts/<delivery_id>/ack")
def contract_ack(delivery_id):
    body = request.get_json(force=True)
    delivery = get_session().scalar(
        select(EdgeContractDelivery).where(
            EdgeContractDelivery.delivery_id == delivery_id
        )
    )
    if not delivery:
        raise EdgeError("CONTRACT_DELIVERY_NOT_FOUND", "delivery not found", 404)
    device = get_session().get(EdgeDevice, delivery.edge_device_id)
    _require_edge_identity(device, body)
    state = str(body.get("status", ""))
    if state not in {"DOWNLOADED", "VERIFIED", "ACTIVE", "REJECTED", "FAILED"}:
        raise EdgeError("CONTRACT_ACK_STATE_INVALID", "invalid contract ACK", 422)
    if delivery.status == state:
        get_session().commit()
        return response({"accepted": True, "idempotent": True, "status": state})
    transitions = {
        "PENDING": {"DOWNLOADED", "VERIFIED", "ACTIVE", "REJECTED", "FAILED"},
        "DELIVERED": {"DOWNLOADED", "VERIFIED", "ACTIVE", "REJECTED", "FAILED"},
        "DOWNLOADED": {"VERIFIED", "ACTIVE", "REJECTED", "FAILED"},
        "VERIFIED": {"ACTIVE", "REJECTED", "FAILED"},
        "ACTIVE": {"ACTIVE"},
        "REJECTED": {"REJECTED"},
        "FAILED": {"FAILED"},
    }
    if state not in transitions.get(delivery.status, set()):
        raise EdgeError("CONTRACT_ACK_STATE_CONFLICT", "invalid transition", 409)
    EdgeContractReconciliationService(get_session()).acknowledge(delivery, state)
    get_session().add(
        EdgeAuditLog(
            device_id=device.id,
            company_id=device.company_id,
            action=f"EDGE_CONTRACT_{state}",
            old_values={},
            new_values={"delivery_id": delivery_id},
            correlation_id=correlation_id(),
            ip_address=request.remote_addr,
        )
    )
    get_session().commit()
    return response({"accepted": True, "idempotent": False, "status": state})


@edge_cloud.post("/api/v1/devices/<int:device_id>/hardware-activation")
@require_permission("edge.manage")
def create_hardware_activation(device_id):
    bus = get_session().get(CloudBusDevice, device_id)
    if not bus:
        abort(404)
    device_for_user(bus.edge_device_id)
    action = str(request.get_json(force=True).get("action", ""))
    try:
        delivery = HardwareActivationService(
            get_session(), _contract_signer()
        ).create(
            bus,
            action,
            wait_for_staged=(action == "ACTIVATE_DEVICE_RUNTIME"),
        )
    except (ContractControlError, ConfigurationSigningError) as exc:
        get_session().rollback()
        raise EdgeError(str(exc), "hardware activation denied", 409) from exc
    get_session().add(
        EdgeAuditLog(
            device_id=bus.edge_device_id,
            company_id=bus.company_id,
            user_id=session.get("unified_user_id"),
            action="HARDWARE_ACTIVATION_CREATED",
            old_values={},
            new_values={"delivery_id": delivery.delivery_id, "action": action},
            correlation_id=correlation_id(),
            ip_address=request.remote_addr,
        )
    )
    get_session().commit()
    return response({"delivery_id": delivery.delivery_id, "status": "PENDING"}, 201)


@edge_cloud.get("/api/v1/devices/<int:device_id>/hardware-activation/<delivery_id>")
@require_permission("edge.manage")
def hardware_activation_result(device_id, delivery_id):
    bus = get_session().get(CloudBusDevice, device_id)
    if not bus:
        abort(404)
    device_for_user(bus.edge_device_id)
    delivery = get_session().scalar(select(HardwareActivationDelivery).where(
        HardwareActivationDelivery.device_id == bus.id,
        HardwareActivationDelivery.delivery_id == delivery_id,
    ))
    if not delivery:
        abort(404)
    return response({
        "delivery_id": delivery.delivery_id,
        "status": delivery.status,
        "action": delivery.action,
        "result": delivery.result_json or {},
        "error_code": delivery.error_code,
        "error_message": delivery.error_message,
    })


@edge_cloud.post("/api/v1/edge/hardware-commands/pull")
def hardware_command_pull():
    body = request.get_json(force=True)
    device = get_session().scalar(
        select(EdgeDevice).where(
            EdgeDevice.device_uuid == body.get("edge_device_uuid")
        )
    )
    if not device:
        raise EdgeError("DEVICE_UNKNOWN", "Edge device not found", 404)
    _require_edge_proof(device, body)
    rows = get_session().scalars(
        select(HardwareActivationDelivery)
        .where(
            HardwareActivationDelivery.edge_device_id == device.id,
            HardwareActivationDelivery.status.in_(["PENDING", "DELIVERED"]),
        )
        .order_by(HardwareActivationDelivery.id)
        .limit(20)
    ).all()
    items = []
    for row in rows:
        if _is_expired(row.expires_at):
            row.status = "EXPIRED"
            continue
        items.append(
            {
                "delivery_id": row.delivery_id,
                "payload": row.payload_json,
                "payload_hash": row.payload_hash,
                "envelope": row.signed_envelope_json,
                "signature": row.signature,
                "signature_algorithm": row.signature_algorithm,
                "signing_key_id": row.signing_key_id,
            }
        )
        row.status = "DELIVERED"
        row.attempt_count += 1
    diagnostics = get_session().scalars(
        select(HardwareDiagnosticRun).where(
            HardwareDiagnosticRun.edge_device_id == device.id,
            HardwareDiagnosticRun.status.in_(["PENDING", "DELIVERED"]),
        ).order_by(HardwareDiagnosticRun.id).limit(max(0, 20 - len(items)))
    ).all()
    for row in diagnostics:
        if _is_expired(row.expires_at):
            row.status = "EXPIRED"
            continue
        items.append({
            "delivery_id": row.diagnostic_id,
            "payload": row.payload_json,
            "payload_hash": row.payload_hash,
            "envelope": row.signed_envelope_json,
            "signature": row.signature,
            "signature_algorithm": row.signature_algorithm,
            "signing_key_id": row.signing_key_id,
        })
        row.status = "DELIVERED"
        row.attempt_count += 1
        get_session().add(EdgeAuditLog(
            device_id=device.id, company_id=device.company_id,
            action="DIAGNOSTIC_DELIVERED", old_values={},
            new_values={"diagnostic_id": row.diagnostic_id},
            correlation_id=correlation_id(), ip_address=request.remote_addr,
        ))
    get_session().commit()
    return response({"items": items})


@edge_cloud.post("/api/v1/edge/hardware-commands/<delivery_id>/ack")
def hardware_command_ack(delivery_id):
    body = request.get_json(force=True)
    delivery = get_session().scalar(
        select(HardwareActivationDelivery).where(
            HardwareActivationDelivery.delivery_id == delivery_id
        )
    )
    diagnostic = None
    if not delivery:
        diagnostic = get_session().scalar(select(HardwareDiagnosticRun).where(
            HardwareDiagnosticRun.diagnostic_id == delivery_id
        ))
    if not delivery and not diagnostic:
        raise EdgeError("HARDWARE_DELIVERY_NOT_FOUND", "delivery not found", 404)
    device = get_session().get(
        EdgeDevice, delivery.edge_device_id if delivery else diagnostic.edge_device_id
    )
    _require_edge_identity(device, body)
    state = str(body.get("status", ""))
    states = {
        "RECEIVED",
        "VERIFIED",
        "AUTHORIZED",
        "EXECUTING",
        "SUCCEEDED",
        "FAILED",
        "REJECTED",
    }
    if state not in states:
        raise EdgeError("HARDWARE_ACK_STATE_INVALID", "invalid hardware ACK", 422)
    if diagnostic is not None:
        diagnostic.status = state
        now = utcnow()
        if state == "RECEIVED":
            diagnostic.edge_received_at = now
        elif state == "EXECUTING":
            diagnostic.started_at = now
        elif state in {"SUCCEEDED", "FAILED", "REJECTED"}:
            diagnostic.finished_at = now
        diagnostic.error_code = str(body.get("error_code") or "")[:100] or None
        diagnostic.error_message = str(body.get("error_message") or "")[:500] or None
        result = body.get("result")
        if isinstance(result, dict):
            diagnostic.result_json = result
            if result.get("elapsed_ms") is not None:
                diagnostic.elapsed_ms = result["elapsed_ms"]
            diagnostic.parser_status = str(
                result.get("parser_status") or result.get("probe_status") or ""
            )[:80] or None
            for audit_action, present in (
                ("DIAGNOSTIC_PORT_OPENED", result.get("serial_opened")),
                ("DIAGNOSTIC_TX_SENT", result.get("tx_sent")),
                ("DIAGNOSTIC_RX_RECEIVED", result.get("rx_received")),
            ):
                if present:
                    get_session().add(EdgeAuditLog(
                        device_id=device.id, company_id=device.company_id,
                        action=audit_action, old_values={},
                        new_values={"diagnostic_id": delivery_id},
                        correlation_id=correlation_id(), ip_address=request.remote_addr,
                    ))
        get_session().add(EdgeAuditLog(
            device_id=device.id, company_id=device.company_id,
            action=(
                "DIAGNOSTIC_SUCCEEDED" if state == "SUCCEEDED"
                else "DIAGNOSTIC_FAILED" if state in {"FAILED", "REJECTED"}
                else f"DIAGNOSTIC_{state}"
            ),
            old_values={}, new_values={"diagnostic_id": delivery_id, "status": state},
            correlation_id=correlation_id(), ip_address=request.remote_addr,
        ))
        get_session().commit()
        return response({"accepted": True, "idempotent": False, "status": state})
    if delivery.status == state:
        get_session().commit()
        return response({"accepted": True, "idempotent": True, "status": state})
    delivery.status = state
    delivery.acknowledged_at = utcnow()
    delivery.error_code = str(body.get("error_code") or "")[:100] or None
    delivery.error_message = str(body.get("error_message") or "")[:500] or None
    result = body.get("result")
    if isinstance(result, dict):
        delivery.result_json = result
    bus = get_session().get(CloudBusDevice, delivery.device_id)
    if delivery.action in {"AUTHORIZE_FUELING_PRESET", "LOCK_FUELING_AUTHORIZATION"}:
        pump_command = get_session().scalar(select(PumpCommand).where(PumpCommand.command_id == delivery.delivery_id))
        fueling = get_session().get(FuelingSession, pump_command.fueling_session_id) if pump_command else None
        if pump_command:
            pump_command.status = state
            pump_command.response_json = result if isinstance(result, dict) else {}
            pump_command.error_message = delivery.error_message
        if fueling:
            mapped = {"RECEIVED": "EDGE_RECEIVED", "VERIFIED": "EDGE_RECEIVED",
                "AUTHORIZED": "PUMP_WAITING", "EXECUTING": "PUMP_WAITING",
                "SUCCEEDED": "PUMP_AUTHORIZED", "FAILED": "FAILED", "REJECTED": "FAILED"}
            if delivery.action == "AUTHORIZE_FUELING_PRESET":
                fueling.status = mapped[state]
                fueling.event_version += 1
                if state == "SUCCEEDED": fueling.authorized_at = utcnow()
                if state in {"FAILED", "REJECTED"}:
                    fueling.failure_code = delivery.error_code or "EDGE_COMMAND_FAILED"
                    fueling.failure_message = delivery.error_message
                    fueling.completed_at = utcnow()
                hold_released = _release_rejected_fueling_hold(
                    get_session(), fueling, delivery
                )
            else:
                hold_released = False
            get_session().add(CustomerRealtimeEvent(customer_id=fueling.customer_id,
                event_type="FUELING_SESSION_UPDATED", entity_id=fueling.public_id,
                event_version=fueling.event_version,
                payload_json={"sessionId": fueling.public_id, "status": fueling.status}))
            get_session().add(CustomerAuditEvent(customer_id=fueling.customer_id,
                company_id=fueling.company_id, station_id=fueling.station_id,
                fueling_session_id=fueling.id, correlation_id=str(delivery.payload_json.get("correlation_id") or correlation_id()),
                action=("PUMP_AUTHORIZATION_ACKNOWLEDGED" if state == "SUCCEEDED" else
                        "FUELING_FAILED" if state in {"FAILED", "REJECTED"} else f"EDGE_COMMAND_{state}"),
                entity_type="fueling_session", entity_id=fueling.public_id,
                details_json={"delivery_id": delivery.delivery_id, "action": delivery.action,
                    "hold_released": hold_released}, source="EDGE"))
    if state == "SUCCEEDED":
        if delivery.action == "ACTIVATE_DEVICE_RUNTIME":
            bus.activation_status = "ACTIVE"
            bus.hardware_active = True
            bus.deployment_status = "ACTIVE"
            bus.status = "ACTIVE"
            config = get_session().get(
                DeviceConfigurationVersion, delivery.configuration_version_id
            )
            definition = (
                (config.configuration_json or {}).get("configuration") or {}
                if config else {}
            )
            if bus.device_type == "FUEL_PUMP" and definition.get("pump_id"):
                pump = get_session().get(Pump, int(definition["pump_id"]))
                if pump is not None:
                    pump.status = "ACTIVE"
                    pump.enabled = True
                    pump.last_seen_at = utcnow()
        elif delivery.action == "DEACTIVATE_DEVICE_RUNTIME":
            bus.activation_status = "NOT_ACTIVATED"
            bus.hardware_active = False
            bus.deployment_status = "STAGED"
        elif delivery.action == "DECOMMISSION_DEVICE":
            bus.activation_status = "NOT_ACTIVATED"
            bus.hardware_active = False
            bus.deployment_status = "DECOMMISSIONED"
            bus.configuration_status = "DECOMMISSIONED"
            bus.status = "DECOMMISSIONED"
            config = get_session().get(
                DeviceConfigurationVersion, delivery.configuration_version_id
            )
            definition = (
                (config.configuration_json or {}).get("configuration") or {}
                if config else {}
            )
            if bus.device_type == "FUEL_PUMP" and definition.get("pump_id"):
                pump = get_session().get(Pump, int(definition["pump_id"]))
                if pump is not None:
                    pump.status = "DECOMMISSIONED"
                    pump.enabled = False
    elif state in {"FAILED", "REJECTED"} and delivery.action in {
        "ACTIVATE_DEVICE_RUNTIME",
        "DEACTIVATE_DEVICE_RUNTIME",
        "DECOMMISSION_DEVICE",
    }:
        bus.activation_status = state
        bus.hardware_active = False
    get_session().commit()
    return response({"accepted": True, "idempotent": False, "status": state})


@edge_cloud.get("/api/v1/edge/openapi.json")
def edge_openapi():
    return response({
        "openapi": "3.0.3",
        "info": {"title": "NNEXORIS Edge Enrollment API", "version": "1.1"},
        "paths": {
            "/api/v1/edge/pairing/sessions": {"post": {"summary": "Enroll Edge identity; delivery credential is returned once"}},
            "/api/v1/edge/pairing/status": {"get": {"summary": "Read pairing and safe assignment status"}},
            "/api/v1/edge/pairing/confirm": {"post": {"summary": "Confirm assignment locally"}},
            "/api/v1/edge/activation": {"post": {"summary": "Retrieve activation bundle with Ed25519 device proof"}},
            "/api/v1/edge/activation/confirm": {"post": {"summary": "Confirm one-time activation token"}},
            "/api/v1/edge/heartbeat": {"post": {"summary": "Submit signed heartbeat"}},
            "/api/v1/edge/trust/configuration-signing-keys": {"post": {"summary": "Refresh pinned public configuration signing keys using Device Proof"}},
            "/api/v1/edge/devices/{edge_device_id}/serial-ports/sync": {"post": {"summary": "Submit authenticated serial inventory"}},
            "/api/v1/edge-devices/{edge_device_id}/serial-ports": {"get": {"summary": "List Edge serial ports"}},
            "/api/v1/edge-devices/{edge_device_id}/serial-ports/{port_id}/devices": {"get": {"summary": "List devices on a port"}},
            "/api/v1/edge-devices/{edge_device_id}/port-configurations": {"post": {"summary": "Create signed staged configuration"}},
            "/api/v1/edge/configurations/pull": {"post": {"summary": "Pull authenticated staged configurations"}},
            "/api/v1/edge/configurations/{delivery_id}/ack": {"post": {"summary": "Acknowledge validated or staged configuration"}},
            "/api/v1/edge/protocols/pull": {"post": {"summary": "Pull required signed published protocol versions"}},
            "/api/v1/edge/protocols/{protocol_delivery_id}/ack": {"post": {"summary": "Acknowledge downloaded or verified protocol delivery"}},
            "/api/v1/edge/events/batch": {"post": {"summary": "Ingest idempotent prioritized Edge events"}},
            "/api/v1/edge/contracts/pull": {"post": {"summary": "Pull signed persistent Edge contract"}},
            "/api/v1/edge/contracts/{delivery_id}/ack": {"post": {"summary": "Acknowledge and activate Edge contract"}},
            "/api/v1/edge/hardware-commands/pull": {"post": {"summary": "Pull signed semantic hardware commands"}},
            "/api/v1/edge/hardware-commands/{delivery_id}/ack": {"post": {"summary": "Acknowledge hardware command state"}},
        },
        "components": {"schemas": {
            "DeviceProof": {"type": "object", "required": ["algorithm", "public_key_fingerprint", "signature"]},
            "TrustSigningKeysResponse": {"type": "object", "required": ["edge_device_uuid", "keys"]},
            "InventorySyncRequest": {"type": "object", "required": ["edge_device_uuid", "sync_id", "inventory_version", "ports", "timestamp", "nonce", "request_id", "body_hash", "device_proof"]},
            "InventorySyncResponse": {"type": "object", "required": ["accepted", "sync_id", "inventory_version"]},
            "ConfigurationPullRequest": {"type": "object", "required": ["edge_device_uuid", "timestamp", "nonce", "request_id", "body_hash", "device_proof"]},
            "ConfigurationEnvelope": {"type": "object", "required": ["schema_version", "delivery_id", "configuration_version_id", "edge_device_uuid", "configuration"]},
            "SignedConfigurationDelivery": {"type": "object", "required": ["envelope", "configuration_hash", "signature", "signature_algorithm", "signing_key_id"]},
            "ConfigurationAckRequest": {"type": "object", "required": ["edge_device_uuid", "timestamp", "nonce", "request_id", "body_hash", "device_proof", "status"]},
            "ConfigurationAckResponse": {"type": "object", "required": ["accepted", "delivery_id", "status"]},
            "ProtocolPullRequest": {"type": "object", "required": ["edge_device_uuid", "installed_protocols", "supported_schema_versions", "timestamp", "nonce", "request_id", "body_hash", "device_proof"]},
            "SignedProtocolDelivery": {"type": "object", "required": ["protocol_delivery_id", "protocol_code", "protocol_version_id", "version", "definition_hash", "envelope", "signature", "signature_algorithm", "signing_key_id"]},
            "ProtocolAckRequest": {"type": "object", "required": ["edge_device_uuid", "protocol_version_id", "definition_hash", "status", "timestamp", "nonce", "request_id", "body_hash", "device_proof"]},
            "EdgeEventBatchRequest": {"type": "object", "required": ["edge_device_uuid", "events", "timestamp", "nonce", "request_id", "body_hash", "device_proof"]},
            "EdgeContractDefinition": {"type": "object", "required": ["contract_code", "version", "edge_device_uuid", "edge_public_fingerprint", "company_id", "station_id", "hardware_policy", "port_policy", "protocol_policy", "command_policy", "offline_policy", "persistent_autostart_policy", "sync_policy"]},
            "SignedEdgeContract": {"type": "object", "required": ["definition_json", "definition_hash", "envelope", "signature", "signature_algorithm", "signing_key_id"]},
            "ContractPullRequest": {"type": "object", "required": ["edge_device_uuid", "timestamp", "nonce", "request_id", "body_hash", "device_proof"]},
            "ContractAckRequest": {"type": "object", "required": ["edge_device_uuid", "status", "timestamp", "nonce", "request_id", "body_hash", "device_proof"]},
            "HardwareActivationDelivery": {"type": "object", "required": ["delivery_id", "payload", "payload_hash", "envelope", "signature", "signature_algorithm", "signing_key_id"]},
            "HardwareCommandPullRequest": {"type": "object", "required": ["edge_device_uuid", "timestamp", "nonce", "request_id", "body_hash", "device_proof"]},
            "HardwareCommandAckRequest": {"type": "object", "required": ["edge_device_uuid", "status", "timestamp", "nonce", "request_id", "body_hash", "device_proof"]},
            "ErrorResponse": {"type": "object", "required": ["code", "message", "retryable", "correlation_id"]},
        }, "securitySchemes": {
            "DeviceProof": {"type": "apiKey", "in": "body", "name": "device_proof"},
            "IdempotencyKey": {"type": "apiKey", "in": "header", "name": "Idempotency-Key"},
        }},
        "x-nnexoris": {
            "clock_skew_seconds": 300,
            "activation_canonical_prefix": "NNEXORIS-ACTIVATION-V1",
            "confirmation_canonical_prefix": "NNEXORIS-ACTIVATION-CONFIRM-V1",
            "heartbeat_canonical_prefix": "NNEXORIS-HEARTBEAT-V1",
        },
    })


@edge_cloud.post("/api/v1/edge/enrollment/cancel")
def cancel_enrollment():
    body = request.get_json(force=True)
    row = get_session().scalar(select(EdgePairingSession).where(EdgePairingSession.pairing_session_id == body["pairing_session_id"]))
    if not row: raise EdgeError("PAIRING_INVALID", "pairing session not found", 404)
    if row.status not in {"PAIRING_REJECTED", "PAIRING_EXPIRED"}:
        row.status, row.cancelled_at = "PAIRING_REJECTED", __import__("app.models", fromlist=["utcnow"]).utcnow()
        device = get_session().get(EdgeDevice, row.device_id); device.status = "PAIRING_REJECTED"; get_session().commit()
    return response({"status": row.status})


@edge_cloud.get("/api/v1/edge-devices/preview")
@require_permission("edge.device.claim")
def preview_pairing():
    return response(service().preview(request.args.get("pairing_code", "")))


@edge_cloud.get("/api/v1/edge-devices")
@require_permission("edge.device.view")
def devices_api():
    require_edge_schema()
    rows = service().visible_devices(current_company_id(), normalize_role(session.get("unified_role")) == "Super Admin")
    sensitive = has_permission("edge.device.view_sensitive")
    return response({"items": [serialize_device(row, sensitive) for row in rows], "total": len(rows)})


@edge_cloud.post("/api/v1/edge-devices/claim")
@edge_cloud.post("/api/v1/edge/pairing/claim")
@require_permission("edge.device.claim")
def claim():
    return response(service().claim(request.get_json(force=True), session.get("unified_user_id"), current_company_id(),
        normalize_role(session.get("unified_role")) == "Super Admin", request.headers.get("Idempotency-Key"), correlation_id()), 201)


@edge_cloud.get("/api/v1/edge-devices/unclaimed")
@require_permission("edge.device.super_admin_view")
def unclaimed():
    if normalize_role(session.get("unified_role")) != "Super Admin": abort(403)
    rows = get_session().scalars(select(EdgeDevice).where(EdgeDevice.company_id.is_(None))).all()
    return response({"items": [serialize_device(row, True) for row in rows]})


@edge_cloud.get("/api/v1/edge-devices/pending")
@require_permission("edge.device.view")
def pending():
    rows = [d for d in service().visible_devices(current_company_id(), normalize_role(session.get("unified_role")) == "Super Admin")
            if d.status in {"PAIRING_REQUESTED", "PENDING_LOCAL_CONFIRMATION", "PENDING_CLOUD_APPROVAL", "APPROVED", "ACTIVATING"}]
    return response({"items": [serialize_device(row) for row in rows]})


@edge_cloud.get("/api/v1/edge-devices/offline")
@require_permission("edge.device.view")
def offline():
    rows = [d for d in service().visible_devices(current_company_id(), normalize_role(session.get("unified_role")) == "Super Admin")
            if _effective_connectivity(d) in {"OFFLINE", "STALE"}]
    return response({"items": [serialize_device(row) for row in rows]})


@edge_cloud.get("/api/v1/edge-devices/<int:device_id>")
@require_permission("edge.device.view")
def device_detail_api(device_id):
    return response(serialize_device(device_for_user(device_id), has_permission("edge.device.view_sensitive")))


@edge_cloud.patch("/api/v1/edge-devices/<int:device_id>")
@require_permission("edge.device.update")
def device_update(device_id):
    device, body = device_for_user(device_id), request.get_json(force=True)
    if "name" in body: device.name = str(body["name"]).strip()[:160]
    if "description" in body: device.description = str(body["description"])[:2000]
    get_session().commit(); return response(serialize_device(device))


@edge_cloud.post("/api/v1/edge-devices/<int:device_id>/approve")
@require_permission("edge.device.approve")
def approve(device_id):
    return response(service().approve(device_for_user(device_id), session.get("unified_user_id"), correlation_id()))


@edge_cloud.post("/api/v1/edge-devices/<int:device_id>/assign")
@edge_cloud.post("/api/v1/edge-devices/<int:device_id>/transfer")
@require_permission("edge.device.transfer")
def assign_device(device_id):
    device, body = device_for_user(device_id), request.get_json(force=True)
    if normalize_role(session.get("unified_role")) != "Super Admin": abort(403)
    from app.models import Company, Station
    company, station = get_session().get(Company, int(body["company_id"])), get_session().get(Station, int(body["station_id"]))
    if not company or not company.enabled or not station or station.status != "active" or station.company_id != company.id:
        raise EdgeError("ASSIGNMENT_INVALID", "active station must belong to active company", 409)
    old = {"company_id": device.company_id, "station_id": device.station_id}
    device.company_id, device.station_id = company.id, station.id
    get_session().add(EdgeAuditLog(device_id=device.id, company_id=company.id, user_id=session.get("unified_user_id"),
        action="edge.device.transfer", old_values=old, new_values={"company_id": company.id, "station_id": station.id},
        correlation_id=correlation_id(), ip_address=request.remote_addr))
    get_session().commit(); return response(serialize_device(device))


@edge_cloud.post("/api/v1/edge-devices/<int:device_id>/<action>")
def lifecycle(device_id, action):
    permission = {"reject": "edge.device.reject", "suspend": "edge.device.suspend", "resume": "edge.device.resume",
        "revoke": "edge.device.revoke", "maintenance": "edge.device.maintenance", "replace": "edge.device.replace"}.get(action)
    if not permission or not has_permission(permission): abort(403)
    body = request.get_json(silent=True) or {}
    if action in {"reject", "suspend", "revoke", "replace"} and not str(body.get("reason", "")).strip():
        raise EdgeError("REASON_REQUIRED", "reason is required")
    targets = {"reject": "PAIRING_REJECTED", "suspend": "SUSPENDED", "resume": "ACTIVE",
        "revoke": "REVOKED", "maintenance": "MAINTENANCE", "replace": "REPLACED"}
    device = device_for_user(device_id)
    from app.edge_cloud.state import transition
    transition(device, targets[action]); get_session().commit()
    return response(serialize_device(device))


@edge_cloud.get("/api/v1/edge-devices/<int:device_id>/health")
@require_permission("edge.device.view_health")
def device_health(device_id):
    device = device_for_user(device_id)
    heartbeat = get_session().scalar(select(EdgeHeartbeat).where(EdgeHeartbeat.device_id == device.id).order_by(EdgeHeartbeat.received_at.desc()))
    return response({"device": serialize_device(device), "snapshot": heartbeat.payload_json_filtered if heartbeat else None})


@edge_cloud.get("/api/v1/edge-devices/<int:device_id>/heartbeats")
@require_permission("edge.device.view_health")
def heartbeats(device_id):
    device = device_for_user(device_id)
    query = select(EdgeHeartbeat).where(EdgeHeartbeat.device_id == device.id)
    raw_from, raw_to = request.args.get("from"), request.args.get("to")
    try:
        date_from = datetime.fromisoformat(raw_from.replace("Z", "+00:00")) if raw_from else None
        date_to = datetime.fromisoformat(raw_to.replace("Z", "+00:00")) if raw_to else None
    except ValueError as exc:
        raise EdgeError("TELEMETRY_RANGE_INVALID", "from and to must be ISO-8601 timestamps", 422) from exc
    now = datetime.now(timezone.utc)
    if date_from and date_from.tzinfo is None: date_from = date_from.replace(tzinfo=timezone.utc)
    if date_to and date_to.tzinfo is None: date_to = date_to.replace(tzinfo=timezone.utc)
    if date_from and date_to and date_to < date_from:
        raise EdgeError("TELEMETRY_RANGE_INVALID", "to must be later than from", 422)
    if date_from and (date_to or now) - date_from > timedelta(days=7):
        raise EdgeError("TELEMETRY_RANGE_TOO_LARGE", "maximum telemetry range is 7 days", 422)
    if date_from: query = query.where(EdgeHeartbeat.received_at >= date_from)
    if date_to: query = query.where(EdgeHeartbeat.received_at <= date_to)
    limit = min(max(request.args.get("limit", 500, type=int), 1), 2000)
    rows = get_session().scalars(query.order_by(EdgeHeartbeat.received_at.desc()).limit(limit)).all()
    return response({"items": [_serialize_heartbeat(row) for row in rows], "total": len(rows)})


@edge_cloud.get("/api/v1/edge-devices/<int:device_id>/events")
@require_permission("edge.device.view_logs")
def events(device_id):
    device = device_for_user(device_id)
    rows = get_session().scalars(select(EdgeDeviceEvent).where(EdgeDeviceEvent.device_id == device.id).order_by(EdgeDeviceEvent.occurred_at.desc()).limit(200)).all()
    return response({"items": [{"type": r.event_type, "severity": r.severity, "message": r.message, "occurred_at": r.occurred_at.isoformat()} for r in rows]})


@edge_cloud.get("/api/v1/edge-devices/<int:device_id>/certificates")
@require_permission("edge.device.manage_certificates")
def certificates(device_id):
    device = device_for_user(device_id)
    rows = get_session().scalars(select(EdgeCertificate).where(EdgeCertificate.device_id == device.id)).all()
    return response({"items": [{"serial": r.certificate_serial, "fingerprint": r.certificate_fingerprint,
        "status": r.status, "issued_at": r.issued_at.isoformat(), "expires_at": r.expires_at.isoformat()} for r in rows]})


@edge_cloud.post("/api/v1/edge-devices/<int:device_id>/certificates/rotate")
@require_permission("edge.device.rotate_certificate")
def rotate_certificate(device_id):
    device = device_for_user(device_id)
    if device.status != "ACTIVE": raise EdgeError("DEVICE_NOT_ACTIVE", "certificate rotation requires an active device", 409)
    provider, now = service().certificates, __import__("app.models", fromlist=["utcnow"]).utcnow()
    for old in get_session().scalars(select(EdgeCertificate).where(
        EdgeCertificate.device_id == device.id, EdgeCertificate.status.in_(["ACTIVE", "FAKE_TEST_ONLY"]))):
        old.status = "ROTATED"
    issued = provider.rotate_device_certificate(device)
    cert = EdgeCertificate(device_id=device.id, certificate_serial=issued.serial,
        certificate_fingerprint=issued.fingerprint, issuer=issued.issuer, subject=issued.subject,
        issued_at=issued.issued_at, expires_at=issued.expires_at, status=issued.status,
        certificate_pem=issued.certificate_pem, chain_pem=issued.chain_pem)
    get_session().add(cert); get_session().commit()
    return response({"serial": cert.certificate_serial, "fingerprint": cert.certificate_fingerprint,
                     "status": cert.status, "expires_at": cert.expires_at.isoformat()}, 201)


@edge_cloud.post("/api/v1/edge/certificates/rotate")
def device_rotate_certificate():
    body = request.get_json(force=True)
    device = get_session().scalar(select(EdgeDevice).where(
        EdgeDevice.device_uuid == body.get("device_uuid"), EdgeDevice.registration_number == body.get("registration_number")))
    if not device: raise EdgeError("DEVICE_UNKNOWN", "unknown device", 404)
    if device.status != "ACTIVE": raise EdgeError("DEVICE_NOT_ACTIVE", "rotation requires active device", 409)
    issued = service().certificates.rotate_device_certificate(device)
    cert = EdgeCertificate(device_id=device.id, certificate_serial=issued.serial,
        certificate_fingerprint=issued.fingerprint, issuer=issued.issuer, subject=issued.subject,
        issued_at=issued.issued_at, expires_at=issued.expires_at, status=issued.status,
        certificate_pem=issued.certificate_pem, chain_pem=issued.chain_pem)
    get_session().add(cert); get_session().commit()
    return response({"serial": cert.certificate_serial, "certificate_pem": cert.certificate_pem,
                     "chain_pem": cert.chain_pem, "status": "FAKE_TEST_ONLY"}, 201)


@edge_cloud.get("/api/v1/edge-devices/<int:device_id>/audit")
@require_permission("edge.device.view_logs")
def device_audit(device_id):
    device = device_for_user(device_id)
    rows = get_session().scalars(select(EdgeAuditLog).where(
        EdgeAuditLog.device_id == device.id).order_by(EdgeAuditLog.created_at.desc()).limit(200)).all()
    return response({"items": [{"action": row.action, "user_id": row.user_id,
        "correlation_id": row.correlation_id, "created_at": row.created_at.isoformat(),
        "old_values": row.old_values, "new_values": row.new_values} for row in rows]})


@edge_cloud.get("/edge-devices")
@require_permission("edge.device.view")
def devices_page():
    if not edge_schema_ready():
        return render_template("unified/edge_devices/index.html", devices=[], schema_ready=False), 503
    rows = service().visible_devices(current_company_id(), normalize_role(session.get("unified_role")) == "Super Admin")
    return render_template(
        "unified/edge_devices/index.html",
        devices=[serialize_device(row, has_permission("edge.device.view_sensitive")) for row in rows],
        schema_ready=True,
        can_claim=has_permission("edge.device.claim"),
    )


@edge_cloud.get("/edge-devices/add")
@require_permission("edge.device.claim")
def add_device_page():
    if not edge_schema_ready():
        return render_template("unified/edge_devices/schema_required.html"), 503
    from app.models import Company, Station
    db = get_session(); is_super = normalize_role(session.get("unified_role")) == "Super Admin"
    companies = db.scalars(select(Company).where(Company.enabled.is_(True))).all() if is_super else []
    stations = db.scalars(select(Station).where(Station.status == "active",
        Station.company_id == current_company_id() if not is_super else Station.id.is_not(None))).all()
    edges = service().visible_devices(current_company_id(), is_super)
    edge_ids = [row.id for row in edges]
    ports = db.scalars(select(EdgeSerialPort).where(
        EdgeSerialPort.edge_device_id.in_(edge_ids) if edge_ids else EdgeSerialPort.id.is_(None)
    ).order_by(EdgeSerialPort.edge_device_id, EdgeSerialPort.stable_identity)).all()
    protocols = db.execute(select(ProtocolProfile, ProtocolVersion).join(
        ProtocolVersion, ProtocolVersion.id == ProtocolProfile.published_version_id
    ).where(
        ProtocolProfile.enabled.is_(True),
        ProtocolVersion.status == "PUBLISHED",
        ProtocolVersion.signature_algorithm == "Ed25519",
        ProtocolVersion.signature != "",
        ProtocolVersion.definition_hash.is_not(None),
    ).order_by(ProtocolProfile.code)).all()
    return render_template("unified/edge_devices/add.html", companies=companies, stations=stations, is_super=is_super,
        tenant_company_id=current_company_id(), hardware_edges=edges,
        hardware_ports=[_port_json(row) for row in ports],
        published_protocols=[{
            "id": profile.id, "code": profile.code, "version_id": version.id,
            "version": version.version, "hash": version.definition_hash,
            "definition": version.definition_json,
        } for profile, version in protocols])


@edge_cloud.get("/edge-devices/<int:device_id>")
@require_permission("edge.device.view")
def device_page(device_id):
    device = device_for_user(device_id)
    pairing = get_session().scalar(select(EdgePairingSession).where(
        EdgePairingSession.device_id == device.id).order_by(EdgePairingSession.id.desc()))
    company = get_session().get(Company, device.company_id) if device.company_id else None
    station = get_session().get(Station, device.station_id) if device.station_id else None
    ports = get_session().scalars(select(EdgeSerialPort).where(
        EdgeSerialPort.edge_device_id == device.id).order_by(EdgeSerialPort.stable_identity)).all()
    bus_devices = get_session().scalars(select(CloudBusDevice).where(
        CloudBusDevice.edge_device_id == device.id).order_by(CloudBusDevice.id)).all()
    installed = get_session().scalars(select(EdgeInstalledProtocol).where(
        EdgeInstalledProtocol.edge_device_id == device.id).order_by(EdgeInstalledProtocol.protocol_code)).all()
    contract = get_session().scalar(select(EdgeContract).where(
        EdgeContract.edge_device_id == device.id))
    contract_version = (
        get_session().get(EdgeContractVersion, contract.current_version_id)
        if contract and contract.current_version_id else None
    )
    if contract and contract_version is None:
        contract_version = get_session().scalar(select(EdgeContractVersion).where(
            EdgeContractVersion.contract_id == contract.id
        ).order_by(EdgeContractVersion.version_number.desc()))
    contract_delivery = (
        get_session().scalar(select(EdgeContractDelivery).where(
            EdgeContractDelivery.contract_id == contract.id
        ).order_by(EdgeContractDelivery.id.desc()))
        if contract else None
    )
    pending_contract_version = (
        get_session().get(EdgeContractVersion, contract_delivery.contract_version_id)
        if contract_delivery and contract_delivery.status == "WAITING_APPROVAL"
        else None
    )
    contract_fallback_hours = max(
        1, int(os.getenv("PETROB_EDGE_CONTRACT_FALLBACK_APPROVAL_HOURS", "24"))
    )
    contract_fallback_eligible_at = (
        contract_delivery.created_at + timedelta(hours=contract_fallback_hours)
        if pending_contract_version and contract_delivery else None
    )
    contract_fallback_allowed = bool(
        pending_contract_version and contract_version
        and is_non_expanding_revision(
            contract_version.definition_json,
            pending_contract_version.definition_json,
        )
    )
    published_protocols = get_session().execute(select(
        ProtocolProfile, ProtocolVersion
    ).join(ProtocolVersion, ProtocolVersion.protocol_profile_id == ProtocolProfile.id).where(
        ProtocolProfile.published_version_id == ProtocolVersion.id,
        ProtocolVersion.status == "PUBLISHED",
        ProtocolVersion.signature_algorithm == "Ed25519",
        ProtocolVersion.signature.is_not(None),
        ProtocolVersion.definition_hash.is_not(None),
    ).order_by(ProtocolProfile.code)).all()
    return render_template(
        "unified/edge_devices/detail.html",
        device=device,
        pairing=pairing,
        company=company,
        station=station,
        can_approve=has_permission("edge.device.approve"),
        can_claim=has_permission("edge.device.claim"),
        can_view_sensitive=has_permission("edge.device.view_sensitive"),
        can_view_health=has_permission("edge.device.view_health"),
        ports=[_port_json(row) for row in ports],
        bus_devices=[_device_json(row) for row in bus_devices],
        installed_protocols=installed,
        edge_contract=contract,
        edge_contract_version=contract_version,
        edge_contract_delivery=contract_delivery,
        edge_contract_pending_version=pending_contract_version,
        contract_fallback_hours=contract_fallback_hours,
        contract_fallback_eligible_at=contract_fallback_eligible_at,
        contract_fallback_allowed=contract_fallback_allowed,
        can_manage_contract=has_permission("edge.manage"),
        is_super_admin=normalize_role(session.get("unified_role")) == "Super Admin",
        contract_protocols=[{
            "code": profile.code,
            "version": version.version,
        } for profile, version in published_protocols],
    )


@edge_cloud.get("/edge-devices/<int:device_id>/ports-devices")
@require_permission("edge.device.view")
def ports_devices_page(device_id):
    device_for_user(device_id)
    return redirect(url_for("edge_cloud.device_page", device_id=device_id, _anchor="ports"), code=302)


@edge_cloud.get("/edge-ports")
@require_permission("edge.device.view")
def ports_page():
    is_super = normalize_role(session.get("unified_role")) == "Super Admin"
    edges = service().visible_devices(current_company_id(), is_super)
    edge_ids = [row.id for row in edges]
    ports = get_session().scalars(select(EdgeSerialPort).where(
        EdgeSerialPort.edge_device_id.in_(edge_ids) if edge_ids else EdgeSerialPort.id.is_(None)
    ).order_by(EdgeSerialPort.edge_device_id, EdgeSerialPort.stable_identity)).all()
    edge_map = {row.id: serialize_device(row) for row in edges}
    serialized = []
    for row in ports:
        item = _port_json(row)
        item["edge"] = edge_map.get(row.edge_device_id)
        serialized.append(item)
    return render_template("unified/edge_devices/ports.html", ports=serialized,
        edges=list(edge_map.values()), can_edit=has_permission("edge.device.update"))


@edge_cloud.get("/edge-fleet")
@require_permission("edge.device.super_admin_view")
def fleet_page():
    if normalize_role(session.get("unified_role")) != "Super Admin": abort(403)
    rows = service().visible_devices(None, True)
    counts = {key: sum(1 for row in rows if row.status == key) for key in ("ACTIVE", "SUSPENDED", "REVOKED")}
    counts.update(total=len(rows), online=sum(1 for row in rows if _effective_connectivity(row) == "ONLINE"),
                  offline=sum(1 for row in rows if _effective_connectivity(row) in {"OFFLINE", "STALE"}),
                  unclaimed=sum(1 for row in rows if row.company_id is None))
    return render_template("unified/edge_devices/fleet.html", devices=rows, counts=counts)
