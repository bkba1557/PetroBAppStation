import hashlib
from datetime import timedelta
from decimal import Decimal, InvalidOperation
from uuid import uuid4

from flask import current_app, g, jsonify, request
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.extensions import get_session
from app.models import (
    CloudBusDevice, Company, CustomerQrResolution, CustomerQrToken, CustomerWallet, EdgeAssignment, FuelingSession, Nozzle,
    Pump, PumpCommand, RFIDSubscription, ShiftSession, Station, Vehicle, WalletHold,
    WalletTransaction, utcnow,
)

from . import customer_api
from .common import api_error, audit, emit
from .security import customer_required, expired
from app.edge_cloud.config_signing import ConfigurationSigningService
from app.edge_cloud.contracts import ContractControlError, HardwareActivationService


ACTIVE_STATES = (
    "CREATED", "AWAITING_FUNDS", "FUNDS_HELD", "QR_RESOLVED",
    "AUTHORIZATION_QUEUED", "EDGE_RECEIVED", "PUMP_WAITING", "PUMP_AUTHORIZED",
    "READY_TO_FUEL", "FUELING", "STOP_REQUESTED", "COMPLETED",
    "SETTLEMENT_PENDING", "REFUND_PENDING",
)


def _hardware_address(value):
    """Canonical hexadecimal address without changing protocol data."""
    raw = str(value or "").strip().lower()
    if raw.startswith("0x"):
        raw = raw[2:]
    try:
        return format(int(raw, 16), "x")
    except (TypeError, ValueError):
        return ""


def _matching_hardware_targets(buses, pump, nozzle):
    """Match by pump address because nozzle identities repeat per pump."""
    pump_address = _hardware_address(pump.device_address)
    if not pump_address:
        return []
    matches = []
    for bus in buses:
        if _hardware_address(bus.device_address) != pump_address:
            continue
        for configured in (bus.protocol_config_json or {}).get("nozzles", []):
            if (str(configured.get("id")) == str(nozzle.nozzle_id)
                    and str(configured.get("fuel_code") or "").lower()
                    == str(nozzle.fuel_code or "").lower()):
                matches.append((bus, configured))
    return matches


def _active_hardware_buses(db, station_id, edge_device_id):
    return db.scalars(select(CloudBusDevice).where(
        CloudBusDevice.station_id == station_id,
        CloudBusDevice.edge_device_id == edge_device_id,
        CloudBusDevice.device_type == "FUEL_PUMP",
        CloudBusDevice.status == "ACTIVE",
        CloudBusDevice.configuration_status == "STAGED",
        CloudBusDevice.hardware_active.is_(True),
    )).all()


def _session_json(db, row):
    station = db.get(Station, row.station_id); pump = db.get(Pump, row.pump_id)
    nozzle = db.get(Nozzle, row.nozzle_id); hold = db.get(WalletHold, row.hold_id) if row.hold_id else None
    return {
        "sessionId": row.public_id, "transactionId": str(row.transaction_id or ""),
        "idempotencyKey": row.idempotency_key, "customerId": g.customer.public_id,
        "stationId": station.station_id, "pumpId": pump.pump_id,
        "nozzleId": nozzle.nozzle_id, "fuelProductId": nozzle.fuel_code,
        "requestedMode": "fixedAmount", "requestedAmount": float(row.requested_amount),
        "maximumAuthorizationAmount": float(row.requested_amount),
        "reservedAmount": float(hold.amount if hold else row.requested_amount),
        "dispensedAmount": float(row.actual_amount or 0), "dispensedVolume": float(row.actual_liters or 0),
        "unitPrice": float(row.unit_price or nozzle.unit_price or 0), "status": row.status,
        "createdAt": row.created_at.isoformat(), "expiresAt": row.expires_at.isoformat(),
        "startedAt": row.fueling_started_at.isoformat() if row.fueling_started_at else None, "completedAt": row.completed_at.isoformat() if row.completed_at else None,
        "failureCode": row.failure_code, "failureMessage": row.failure_message,
        "hardwareActivationEnabled": bool(current_app.config["CUSTOMER_HARDWARE_FUELING_ENABLED"]),
        "activeFuelingStopNotProven": not bool(current_app.config.get("ACTIVE_FUELING_STOP_PROVEN", False)),
    }


@customer_api.post("/qr/resolve")
@customer_required
def qr_resolve():
    db = get_session(); data = request.get_json(silent=True) or {}
    raw_token = str(data.get("token") or "")
    if len(raw_token) < 16:
        return jsonify(valid=False, code="INVALID_QR_TOKEN")
    token = db.scalar(select(CustomerQrToken).where(
        CustomerQrToken.token_hash == hashlib.sha256(raw_token.encode()).hexdigest(),
        CustomerQrToken.enabled.is_(True),
    ))
    now = utcnow()
    if token is None or (token.expires_at and expired(token.expires_at, now)):
        return jsonify(valid=False, code="QR_NOT_FOUND_OR_EXPIRED")
    station = db.get(Station, token.station_id); pump = db.get(Pump, token.pump_id); nozzle = db.get(Nozzle, token.nozzle_id)
    company = db.get(Company, station.company_id) if station else None
    if (station is None or company is None or not company.customer_self_service_enabled or
            not station.customer_self_service_enabled or station.self_service_status not in {"ENABLED", "PILOT", "SCHEDULED"} or station.status != "active" or
            pump is None or nozzle is None or not pump.enabled or not nozzle.enabled):
        return jsonify(valid=False, code="DISPENSER_UNAVAILABLE")
    if current_app.config["CUSTOMER_HARDWARE_FUELING_ENABLED"]:
        edge_id = db.scalar(select(EdgeAssignment.device_id).where(
            EdgeAssignment.station_id == station.id,
            EdgeAssignment.status == "ACTIVE").order_by(EdgeAssignment.id.desc()))
        buses = _active_hardware_buses(db, station.id, edge_id)
        if len(_matching_hardware_targets(buses, pump, nozzle)) != 1:
            return jsonify(valid=False, code="EXACT_HARDWARE_MAPPING_UNAVAILABLE")
    resolution = CustomerQrResolution(public_id=str(uuid4()), customer_id=g.customer.id,
        qr_token_id=token.id, station_id=station.id, pump_id=pump.id, nozzle_id=nozzle.id,
        expires_at=now + timedelta(minutes=5))
    db.add(resolution); db.flush()
    audit("QR_SCANNED", entity_type="qr_resolution", entity_id=resolution.public_id,
          company_id=station.company_id, station_id=station.id,
          details={"pump_id": pump.pump_id, "nozzle_id": nozzle.nozzle_id})
    db.commit()
    return jsonify(valid=True, resolution={"resolutionId": resolution.public_id,
        "stationId": station.station_id, "pumpId": pump.pump_id,
        "nozzleId": nozzle.nozzle_id, "fuelProductId": nozzle.fuel_code,
        "expiresAt": resolution.expires_at.isoformat(), "singleUse": True})


@customer_api.post("/fueling-sessions")
@customer_required
def fueling_create():
    db = get_session(); data = request.get_json(silent=True) or {}
    key = (request.headers.get("Idempotency-Key") or "")[:190]
    if not key:
        return api_error("IDEMPOTENCY_KEY_REQUIRED", 400)
    existing = db.scalar(select(FuelingSession).where(
        FuelingSession.idempotency_key == key, FuelingSession.customer_id == g.customer.id))
    if existing:
        return jsonify(_session_json(db, existing))
    if data.get("requestedMode", "fixedAmount") != "fixedAmount":
        return api_error("CUSTOMER_FULL_TANK_DISABLED", 409)
    try:
        requested = Decimal(str(data.get("requestedAmount"))).quantize(Decimal("0.01"))
    except (InvalidOperation, TypeError):
        return api_error("INVALID_REQUESTED_AMOUNT", 400)
    if requested < Decimal("1.00") or requested > Decimal("1000.00"):
        return api_error("REQUESTED_AMOUNT_OUT_OF_RANGE", 400)
    resolution = db.scalar(select(CustomerQrResolution).where(
        CustomerQrResolution.public_id == str(data.get("qrResolutionId") or ""),
        CustomerQrResolution.customer_id == g.customer.id,
    ).with_for_update())
    now = utcnow()
    if resolution is None or resolution.consumed_at is not None or expired(resolution.expires_at, now):
        return api_error("QR_RESOLUTION_INVALID", 409)
    station = db.get(Station, resolution.station_id)
    company = db.get(Company, station.company_id) if station else None
    pump = db.get(Pump, resolution.pump_id); nozzle = db.get(Nozzle, resolution.nozzle_id)
    scheduled = bool(station and (station.self_service_start_at is None or station.self_service_start_at <= now)
        and (station.self_service_end_at is None or station.self_service_end_at >= now))
    if not (station and company and company.customer_self_service_enabled and station.customer_self_service_enabled
            and station.self_service_status in {"ENABLED", "PILOT", "SCHEDULED"} and scheduled):
        return api_error("SELF_SERVICE_DISABLED", 409)
    if station.self_service_status != "PILOT" or not station.require_operator_confirmation:
        return api_error("PILOT_OPERATOR_SUPERVISION_REQUIRED", 409)
    if not (pump and nozzle and pump.station_id == station.id and nozzle.station_id == station.id
            and nozzle.pump_id == pump.id and pump.enabled and nozzle.enabled
            and pump.status not in {"offline", "disabled"} and nozzle.unit_price):
        return api_error("INVALID_STATION_NOZZLE_MAPPING", 409)
    if requested < Decimal(str(station.minimum_customer_amount)) or requested > Decimal(str(station.maximum_customer_amount)):
        return api_error("REQUESTED_AMOUNT_OUT_OF_RANGE", 400)
    if station.allowed_fuel_types and nozzle.fuel_code not in station.allowed_fuel_types:
        return api_error("FUEL_TYPE_NOT_ALLOWED", 409)
    if db.scalar(select(FuelingSession.id).where(
        FuelingSession.customer_id == g.customer.id, FuelingSession.status.in_(ACTIVE_STATES))):
        return api_error("CUSTOMER_ALREADY_HAS_ACTIVE_SESSION", 409)
    if db.scalar(select(FuelingSession.id).where(
        FuelingSession.station_id == resolution.station_id,
        FuelingSession.pump_id == resolution.pump_id,
        FuelingSession.nozzle_id == resolution.nozzle_id,
        FuelingSession.status.in_(ACTIVE_STATES))):
        return api_error("NOZZLE_ALREADY_HAS_ACTIVE_SESSION", 409)
    shift = db.scalar(select(ShiftSession).where(
        ShiftSession.station_id == resolution.station_id,
        ShiftSession.status == "active", ShiftSession.actual_closed_at.is_(None)))
    if shift is None:
        return api_error("NO_ACTIVE_SHIFT", 409)
    subscription = db.scalar(select(RFIDSubscription).where(
        RFIDSubscription.customer_id == g.customer.id,
        RFIDSubscription.status == "active").order_by(RFIDSubscription.id.desc()))
    wallet = db.scalar(select(CustomerWallet).where(
        CustomerWallet.customer_id == g.customer.id).with_for_update())
    if subscription is None or wallet is None:
        return api_error("CUSTOMER_ACCOUNT_INCOMPLETE", 409)
    available = Decimal(str(wallet.balance)) - Decimal(str(wallet.reserved_balance))
    if available < requested:
        return api_error("INSUFFICIENT_FUNDS", 409)
    vehicle_id = data.get("vehicleId")
    vehicle = db.scalar(select(Vehicle).where(Vehicle.id == int(vehicle_id),
        Vehicle.customer_id == g.customer.id)) if vehicle_id else None
    if vehicle_id and vehicle is None:
        return api_error("VEHICLE_NOT_FOUND", 404)
    if vehicle and vehicle.fuel_code not in {"", "unspecified", nozzle.fuel_code} and not bool(data.get("fuelMismatchConfirmed")):
        return api_error("VEHICLE_FUEL_MISMATCH_CONFIRMATION_REQUIRED", 409)
    edge_id = db.scalar(select(EdgeAssignment.device_id).where(
        EdgeAssignment.station_id == station.id, EdgeAssignment.status == "ACTIVE").order_by(EdgeAssignment.id.desc()))
    hold = WalletHold(public_id=str(uuid4()), wallet_id=wallet.id, customer_id=g.customer.id,
        idempotency_key=f"hold:{key}", amount=requested, captured_amount=0,
        currency=wallet.currency, status="HELD", expires_at=now + timedelta(minutes=10))
    db.add(hold); db.flush()
    wallet.reserved_balance = Decimal(str(wallet.reserved_balance)) + requested
    wallet.version += 1
    db.add(WalletTransaction(company_id=station.company_id, wallet_id=wallet.id,
        transaction_type="FUELING_HOLD", amount=-requested, balance_before=available,
        balance_after=available-requested, reference=hold.public_id,
        idempotency_key=f"hold:{key}", metadata_json={"hold_id": hold.public_id}))
    row = FuelingSession(public_id=str(uuid4()), idempotency_key=key,
        company_id=station.company_id, station_id=resolution.station_id,
        shift_id=shift.id, customer_id=g.customer.id, subscription_id=subscription.id,
        wallet_id=wallet.id, pump_id=resolution.pump_id, nozzle_id=resolution.nozzle_id, edge_device_id=edge_id,
        vehicle_id=vehicle.id if vehicle else None, hold_id=hold.id,
        requested_amount=requested, unit_price=nozzle.unit_price, fuel_code=nozzle.fuel_code,
        status="FUNDS_HELD", source="customer_app",
        expires_at=hold.expires_at, currency=wallet.currency, event_version=1)
    db.add(row); resolution.consumed_at = now
    try:
        db.flush()
        hardware_created = False
        audit("FUELING_SESSION_CREATED", entity_type="fueling_session", entity_id=row.public_id,
              company_id=station.company_id, station_id=station.id, fueling_session_id=row.id,
              details={"hardware_command_created": hardware_created, "fixed_amount_only": True})
        emit(g.customer.id, "FUELING_SESSION_UPDATED", entity_id=row.public_id,
             payload={"sessionId": row.public_id, "status": row.status})
        emit(g.customer.id, "WALLET_UPDATED", entity_id=str(wallet.id), version=wallet.version,
             payload={"walletVersion": wallet.version})
        db.commit()
        return jsonify(_session_json(db, row)), 201
    except IntegrityError:
        db.rollback(); return api_error("ACTIVE_SESSION_CONFLICT", 409)


@customer_api.post("/fueling-sessions/<session_id>/authorize")
@customer_required
def fueling_authorize(session_id):
    """Create one signed semantic authorization after explicit customer confirmation.

    Session creation and wallet holding never call this path.  This handler has
    no serial, SELECT, or raw-protocol knowledge; Edge remains the sole owner
    of the frame and serial transaction.
    """
    db = get_session(); key = (request.headers.get("Idempotency-Key") or "")[:190]
    if not key:
        return api_error("IDEMPOTENCY_KEY_REQUIRED", 400)
    row = db.scalar(select(FuelingSession).where(
        FuelingSession.public_id == session_id, FuelingSession.customer_id == g.customer.id
    ).with_for_update())
    if row is None:
        return api_error("FUELING_SESSION_NOT_FOUND", 404)
    existing = db.scalar(select(PumpCommand).where(
        PumpCommand.fueling_session_id == row.id).with_for_update())
    if existing is not None:
        # A retry must return the same session and must never create another
        # delivery, wallet hold, or authorization frame.
        return jsonify(_session_json(db, row))
    if row.status != "FUNDS_HELD":
        return api_error("SESSION_NOT_READY_FOR_CUSTOMER_CONFIRMATION", 409)
    now = utcnow(); hold = db.get(WalletHold, row.hold_id)
    wallet = db.scalar(select(CustomerWallet).where(CustomerWallet.id == row.wallet_id).with_for_update())
    if hold is None or hold.status != "HELD" or expired(hold.expires_at, now):
        return api_error("WALLET_HOLD_NOT_ACTIVE", 409)
    if wallet is None or Decimal(str(wallet.balance)) < Decimal(str(hold.amount)) or Decimal(str(wallet.reserved_balance)) < Decimal(str(hold.amount)):
        return api_error("INSUFFICIENT_AVAILABLE_BALANCE", 409)
    station = db.get(Station, row.station_id); company = db.get(Company, row.company_id)
    pump = db.get(Pump, row.pump_id); nozzle = db.get(Nozzle, row.nozzle_id)
    scheduled = bool(station and (station.self_service_start_at is None or station.self_service_start_at <= now)
        and (station.self_service_end_at is None or station.self_service_end_at >= now))
    if not (station and company and pump and nozzle and company.customer_self_service_enabled
            and station.customer_self_service_enabled and station.self_service_status == "PILOT"
            and station.require_operator_confirmation and scheduled and station.status == "active"
            and pump.enabled and nozzle.enabled and pump.status not in {"offline", "disabled"}):
        return api_error("SELF_SERVICE_OR_PUMP_UNAVAILABLE", 409)
    if row.expires_at <= now:
        return api_error("FUELING_SESSION_EXPIRED", 409)
    if str(nozzle.fuel_code) != str(row.fuel_code) or nozzle.pump_id != pump.id:
        return api_error("EXACT_PUMP_NOZZLE_FUEL_MISMATCH", 409)
    if Decimal(str(nozzle.unit_price or 0)).quantize(Decimal("0.01")) != Decimal(str(row.unit_price or 0)).quantize(Decimal("0.01")):
        return api_error("UNIT_PRICE_CHANGED_RECONFIRM_REQUIRED", 409)
    if not current_app.config["CUSTOMER_HARDWARE_FUELING_ENABLED"]:
        return api_error("CUSTOMER_HARDWARE_FUELING_DISABLED", 409)
    buses = _active_hardware_buses(db, station.id, row.edge_device_id)
    matches = _matching_hardware_targets(buses, pump, nozzle)
    if len(matches) != 1:
        return api_error("EXACT_NOZZLE_MAPPING_REQUIRED", 409)
    bus, configured = matches[0]
    semantic = {"fueling_session_id": row.public_id, "customer_id": g.customer.public_id,
        "company_id": station.company_id, "station_id": station.id, "pump_id": pump.pump_id,
        "nozzle_id": nozzle.nozzle_id, "pump_address": str(configured.get("address")),
        "requested_amount": format(Decimal(str(row.requested_amount)), ".2f"),
        "unit_price": format(Decimal(str(row.unit_price)), ".2f"), "fuel_code": nozzle.fuel_code,
        "currency": wallet.currency, "protocol_code": bus.protocol_code, "protocol_version": bus.protocol_version,
        "protocol_hash": bus.protocol_hash, "expires_at": hold.expires_at.isoformat(),
        "idempotency_key": f"authorize:{row.public_id}", "correlation_id": g.customer_correlation_id,
        "session_status": "AUTHORIZATION_QUEUED"}
    try:
        signer = ConfigurationSigningService(current_app.config["CONFIG_SIGNING_PRIVATE_KEY_FILE"],
            current_app.config["CONFIG_SIGNING_PUBLIC_KEY_FILE"], current_app.config["CONFIG_SIGNING_KEY_ID"])
        delivery = HardwareActivationService(db, signer).create_customer_fueling(
            bus, "AUTHORIZE_FUELING_PRESET", semantic)
        row.status = "AUTHORIZATION_QUEUED"; row.authorized_at = now; row.event_version += 1
        db.add(PumpCommand(command_id=delivery.delivery_id, company_id=station.company_id,
            station_id=station.id, shift_id=row.shift_id, customer_id=g.customer.id,
            fueling_session_id=row.id, pump_id=pump.id, nozzle_id=nozzle.id,
            amount=row.requested_amount, status="QUEUED", request_json=semantic, response_json={}))
        audit("FUELING_AUTHORIZATION_REQUESTED", entity_type="fueling_session", entity_id=row.public_id,
              company_id=station.company_id, station_id=station.id, fueling_session_id=row.id,
              details={"hardware_delivery_id": delivery.delivery_id})
        emit(g.customer.id, "FUELING_SESSION_UPDATED", entity_id=row.public_id, version=row.event_version,
             payload={"sessionId": row.public_id, "status": row.status})
        db.commit(); return jsonify(_session_json(db, row))
    except (IntegrityError, ContractControlError):
        db.rollback(); return api_error("AUTHORIZATION_NOT_CREATED", 409)


@customer_api.get("/fueling-sessions/<session_id>")
@customer_required
def fueling_get(session_id):
    db = get_session(); row = db.scalar(select(FuelingSession).where(
        FuelingSession.public_id == session_id, FuelingSession.customer_id == g.customer.id))
    if row is None:
        return api_error("FUELING_SESSION_NOT_FOUND", 404)
    return jsonify(_session_json(db, row))


@customer_api.post("/fueling-sessions/<session_id>/cancel")
@customer_required
def fueling_cancel(session_id):
    db = get_session(); row = db.scalar(select(FuelingSession).where(
        FuelingSession.public_id == session_id, FuelingSession.customer_id == g.customer.id
    ).with_for_update())
    if row is None:
        return api_error("FUELING_SESSION_NOT_FOUND", 404)
    if row.status == "CANCELLED":
        return jsonify(_session_json(db, row))
    if row.status not in {"CREATED", "AWAITING_FUNDS", "FUNDS_HELD", "QR_RESOLVED"}:
        return api_error("SESSION_CANNOT_BE_CANCELLED", 409)
    hold = db.get(WalletHold, row.hold_id); wallet = db.scalar(select(CustomerWallet).where(
        CustomerWallet.id == row.wallet_id).with_for_update())
    if hold and hold.status == "HELD":
        amount = Decimal(str(hold.amount)); before = Decimal(str(wallet.balance)) - Decimal(str(wallet.reserved_balance))
        wallet.reserved_balance = max(Decimal("0"), Decimal(str(wallet.reserved_balance)) - amount)
        wallet.version += 1; hold.status = "RELEASED"; hold.released_at = utcnow()
        db.add(WalletTransaction(company_id=row.company_id, wallet_id=wallet.id,
            transaction_type="HOLD_RELEASE", amount=amount, balance_before=before,
            balance_after=before+amount, reference=hold.public_id,
            idempotency_key=f"release:{request.headers.get('Idempotency-Key') or row.idempotency_key}",
            metadata_json={"hold_id": hold.public_id}))
    row.status = "CANCELLED"; row.event_version += 1; row.completed_at = utcnow()
    emit(g.customer.id, "FUELING_SESSION_UPDATED", entity_id=row.public_id,
         version=row.event_version, payload={"sessionId": row.public_id, "status": row.status})
    audit("SESSION_CANCELED", entity_type="fueling_session", entity_id=row.public_id,
          company_id=row.company_id, station_id=row.station_id, fueling_session_id=row.id)
    db.commit(); return jsonify(_session_json(db, row))
