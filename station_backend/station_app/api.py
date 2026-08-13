import hashlib
import secrets
import time
from datetime import date, datetime, time as datetime_time, timedelta, timezone
from decimal import Decimal, InvalidOperation
from uuid import uuid4
from zoneinfo import ZoneInfo

from flask import Blueprint, current_app, g, jsonify, request
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app.edge_cloud.config_signing import ConfigurationSigningService
from app.edge_cloud.contracts import ContractControlError, HardwareActivationService
from app.models import (
    CloudBusDevice,
    Company,
    CustomerQrToken,
    EdgeAssignment,
    FuelingSession,
    HardwareActivationDelivery,
    Nozzle,
    Pump,
    SaleTransaction,
    ShiftSession,
    Station,
    UnifiedUser,
    utcnow,
)

from .models import (
    StationAppAuditEvent,
    StationAppEmployee,
    StationAppFuelingSession,
    StationAppQrResolution,
    StationAppSession,
)
from .security import (
    SESSION_HOURS,
    employee_required,
    internal_required,
    issue_session,
    password_hash,
    password_lookup_digest,
    password_valid,
)


api = Blueprint("station_api", __name__)
ACTIVE_CUSTOMER_STATES = (
    "CREATED",
    "AWAITING_FUNDS",
    "FUNDS_HELD",
    "QR_RESOLVED",
    "AUTHORIZATION_QUEUED",
    "EDGE_RECEIVED",
    "PUMP_WAITING",
    "PUMP_AUTHORIZED",
    "READY_TO_FUEL",
    "FUELING",
    "STOP_REQUESTED",
    "COMPLETED",
    "SETTLEMENT_PENDING",
    "REFUND_PENDING",
)
OPERATIONAL_EDGE_ASSIGNMENT_STATES = ("APPROVED", "ACTIVE")
PAYMENT_METHODS = {"cash", "network", "other"}
ACTIVE_STATION_APP_STATES = (
    "AUTHORIZATION_QUEUED",
    "EDGE_RECEIVED",
    "PUMP_AUTHORIZED",
    "FUELING",
    "COMPLETED_AWAITING_PAYMENT",
    "CANCELLATION_QUEUED",
    "CANCELLATION_FAILED",
)


def _json_error(code: str, status: int, **extra):
    return jsonify(error=code, **extra), status


def _audit(action: str, *, fueling=None, details=None):
    employee = getattr(g, "employee", None)
    g.db.add(
        StationAppAuditEvent(
            employee_id=employee.id if employee else None,
            company_id=(fueling.company_id if fueling else getattr(employee, "company_id", None)),
            station_id=(fueling.station_id if fueling else getattr(employee, "station_id", None)),
            fueling_session_id=fueling.id if fueling else None,
            action=action,
            correlation_id=str(uuid4()),
            ip_address=(
                request.headers.get("X-Forwarded-For") or request.remote_addr or ""
            )[:80],
            details_json=details or {},
        )
    )


def _employee_json(employee, station=None):
    station = station or g.db.get(Station, employee.station_id)
    return {
        "id": employee.public_id,
        "name": employee.name,
        "enabled": employee.enabled,
        "station": {
            "id": station.station_id,
            "nameAr": station.name_ar,
            "nameEn": station.name_en,
        },
        "sessionHours": SESSION_HOURS,
    }


def _fueling_json(row):
    pump = g.db.get(Pump, row.pump_id)
    nozzle = g.db.get(Nozzle, row.nozzle_id)
    return {
        "id": row.public_id,
        "status": row.status,
        "pumpId": pump.pump_id,
        "pumpNumber": pump.pump_number,
        "nozzleId": nozzle.nozzle_id,
        "nozzleNumber": nozzle.nozzle_number,
        "fuelCode": row.fuel_code,
        "fuelColor": nozzle.fuel_color,
        "requestedAmount": float(row.requested_amount),
        "fuelingMode": row.fueling_mode,
        "actualAmount": float(row.actual_amount or 0),
        "actualLiters": float(row.actual_liters or 0),
        "unitPrice": float(row.unit_price),
        "paymentMethod": row.payment_method,
        "paymentOtherReason": row.payment_other_reason,
        "createdAt": row.created_at.isoformat(),
        "completedAt": row.completed_at.isoformat() if row.completed_at else None,
        "expiresAt": row.expires_at.isoformat(),
        "failureCode": row.failure_code,
        "failureMessage": row.failure_message,
    }


@api.get("/health")
def health():
    g.db.execute(select(1))
    return jsonify(status="ok", service="nnexoris-app-station")


@api.post("/api/v1/auth/login")
def login():
    data = request.get_json(silent=True) or {}
    password = str(data.get("password") or "")
    if not 6 <= len(password) <= 128:
        time.sleep(0.25)
        return _json_error("INVALID_CREDENTIALS", 401)
    employee = g.db.scalar(
        select(StationAppEmployee).where(
            StationAppEmployee.password_lookup_digest
            == password_lookup_digest(password)
        )
    )
    now = utcnow()
    if employee is None or not employee.enabled or not password_valid(
        employee.password_hash, password
    ):
        time.sleep(0.25)
        return _json_error("INVALID_CREDENTIALS", 401)
    if employee.locked_until and _aware(employee.locked_until) > now:
        return _json_error("ACCOUNT_TEMPORARILY_LOCKED", 423)
    employee.failed_login_count = 0
    employee.locked_until = None
    employee.last_login_at = now
    token, session_row = issue_session(g.db, employee)
    _audit("EMPLOYEE_LOGIN")
    g.db.commit()
    return jsonify(
        accessToken=token,
        tokenType="Bearer",
        expiresIn=SESSION_HOURS * 3600,
        expiresAt=session_row.expires_at.isoformat(),
        employee=_employee_json(employee),
    )


@api.post("/api/v1/auth/logout")
@employee_required
def logout():
    g.employee_session.revoked_at = utcnow()
    g.employee_session.revoke_reason = "LOGOUT"
    _audit("EMPLOYEE_LOGOUT")
    g.db.commit()
    return jsonify(ok=True)


@api.get("/api/v1/me")
@employee_required
def me():
    return jsonify(employee=_employee_json(g.employee))


@api.get("/api/v1/pumps")
@employee_required
def pumps():
    rows = g.db.scalars(
        select(Pump)
        .where(
            Pump.station_id == g.employee.station_id,
            Pump.deleted_at.is_(None),
        )
        .order_by(Pump.display_order, Pump.pump_number)
    ).all()
    result = []
    for pump in rows:
        nozzles = g.db.scalars(
            select(Nozzle)
            .where(
                Nozzle.station_id == g.employee.station_id,
                Nozzle.pump_id == pump.id,
                Nozzle.deleted_at.is_(None),
            )
            .order_by(Nozzle.display_order, Nozzle.nozzle_number)
        ).all()
        result.append(
            {
                "id": pump.pump_id,
                "number": pump.pump_number,
                "nameAr": pump.name_ar,
                "nameEn": pump.name_en or pump.name_ar,
                "color": pump.color,
                "enabled": pump.enabled,
                "status": pump.status,
                "nozzles": [
                    {
                        "id": nozzle.nozzle_id,
                        "number": nozzle.nozzle_number,
                        "name": nozzle.name,
                        "fuelCode": nozzle.fuel_code,
                        "fuelType": nozzle.fuel_type,
                        "fuelColor": nozzle.fuel_color,
                        "unitPrice": float(nozzle.unit_price or 0),
                        "enabled": nozzle.enabled,
                        "status": nozzle.status,
                    }
                    for nozzle in nozzles
                ],
            }
        )
    return jsonify(pumps=result)


@api.post("/api/v1/qr/resolve")
@employee_required
def resolve_qr():
    raw_token = str((request.get_json(silent=True) or {}).get("token") or "")
    if len(raw_token) < 16:
        return _json_error("INVALID_QR_TOKEN", 400)
    token = g.db.scalar(
        select(CustomerQrToken).where(
            CustomerQrToken.token_hash
            == hashlib.sha256(raw_token.encode()).hexdigest(),
            CustomerQrToken.enabled.is_(True),
        )
    )
    now = utcnow()
    if token is None or (token.expires_at and _aware(token.expires_at) <= now):
        return _json_error("QR_NOT_FOUND_OR_EXPIRED", 404)
    if token.station_id != g.employee.station_id:
        return _json_error("QR_BELONGS_TO_ANOTHER_STATION", 403)
    station = g.db.get(Station, token.station_id)
    pump = g.db.get(Pump, token.pump_id)
    nozzle = g.db.get(Nozzle, token.nozzle_id)
    if not _dispenser_available(station, pump, nozzle):
        return _json_error("DISPENSER_UNAVAILABLE", 409)
    row = StationAppQrResolution(
        public_id=str(uuid4()),
        employee_id=g.employee.id,
        qr_token_id=token.id,
        station_id=station.id,
        pump_id=pump.id,
        nozzle_id=nozzle.id,
        expires_at=now + timedelta(minutes=5),
    )
    g.db.add(row)
    _audit(
        "QR_RESOLVED",
        details={"pump_id": pump.pump_id, "nozzle_id": nozzle.nozzle_id},
    )
    g.db.commit()
    return jsonify(
        valid=True,
        resolution={
            "id": row.public_id,
            "stationId": station.station_id,
            "pumpId": pump.pump_id,
            "pumpNumber": pump.pump_number,
            "nozzleId": nozzle.nozzle_id,
            "nozzleNumber": nozzle.nozzle_number,
            "fuelCode": nozzle.fuel_code,
            "fuelType": nozzle.fuel_type,
            "fuelColor": nozzle.fuel_color,
            "unitPrice": float(nozzle.unit_price or 0),
            "expiresAt": row.expires_at.isoformat(),
        },
    )


@api.post("/api/v1/fueling-sessions")
@employee_required
def start_fueling():
    key = (request.headers.get("Idempotency-Key") or "")[:150]
    if not key:
        return _json_error("IDEMPOTENCY_KEY_REQUIRED", 400)
    scoped_key = f"employee:{g.employee.id}:{key}"
    existing = g.db.scalar(
        select(StationAppFuelingSession).where(
            StationAppFuelingSession.idempotency_key == scoped_key
        )
    )
    if existing:
        _reconcile(existing)
        g.db.commit()
        return jsonify(session=_fueling_json(existing))
    data = request.get_json(silent=True) or {}
    fueling_mode = str(data.get("fuelingMode") or "PRESET").upper()
    if fueling_mode not in {"PRESET", "FULL_TANK"}:
        return _json_error("INVALID_FUELING_MODE", 400)
    if fueling_mode == "FULL_TANK":
        amount = Decimal(str(current_app.config["MAX_FUELING_AMOUNT"]))
    else:
        try:
            amount = Decimal(str(data.get("requestedAmount"))).quantize(
                Decimal("0.01")
            )
        except (InvalidOperation, TypeError):
            return _json_error("INVALID_AMOUNT", 400)
        if amount < Decimal("1.00") or amount > Decimal(
            str(current_app.config["MAX_FUELING_AMOUNT"])
        ):
            return _json_error("AMOUNT_OUT_OF_RANGE", 400)
    resolution = g.db.scalar(
        select(StationAppQrResolution)
        .where(
            StationAppQrResolution.public_id
            == str(data.get("qrResolutionId") or ""),
            StationAppQrResolution.employee_id == g.employee.id,
        )
        .with_for_update()
    )
    now = utcnow()
    if (
        resolution is None
        or resolution.consumed_at is not None
        or _aware(resolution.expires_at) <= now
    ):
        return _json_error("QR_RESOLUTION_INVALID", 409)
    station = g.db.get(Station, resolution.station_id)
    pump = g.db.get(Pump, resolution.pump_id)
    nozzle = g.db.get(Nozzle, resolution.nozzle_id)
    if not _dispenser_available(station, pump, nozzle):
        return _json_error("DISPENSER_UNAVAILABLE", 409)
    shift = g.db.scalar(
        select(ShiftSession).where(
            ShiftSession.station_id == station.id,
            ShiftSession.status == "active",
            ShiftSession.actual_closed_at.is_(None),
        )
    )
    if shift is None:
        return _json_error("NO_ACTIVE_SHIFT", 409)
    customer_conflict = g.db.scalar(
        select(FuelingSession.id).where(
            FuelingSession.station_id == station.id,
            FuelingSession.pump_id == pump.id,
            FuelingSession.nozzle_id == nozzle.id,
            FuelingSession.status.in_(ACTIVE_CUSTOMER_STATES),
        )
    )
    if customer_conflict:
        return _json_error("NOZZLE_BUSY", 409)
    station_app_conflict = g.db.scalar(
        select(StationAppFuelingSession.id).where(
            StationAppFuelingSession.station_id == station.id,
            StationAppFuelingSession.pump_id == pump.id,
            StationAppFuelingSession.nozzle_id == nozzle.id,
            StationAppFuelingSession.status.in_(ACTIVE_STATION_APP_STATES),
        )
    )
    if station_app_conflict:
        return _json_error("NOZZLE_BUSY", 409)
    edge_id = g.db.scalar(
        select(EdgeAssignment.device_id)
        .where(
            EdgeAssignment.station_id == station.id,
            EdgeAssignment.status.in_(OPERATIONAL_EDGE_ASSIGNMENT_STATES),
        )
        .order_by(EdgeAssignment.id.desc())
    )
    matches = _matching_hardware_targets(
        _active_hardware_buses(station.id, edge_id), pump, nozzle
    )
    if len(matches) != 1:
        return _json_error("EXACT_HARDWARE_MAPPING_REQUIRED", 409)
    bus, configured = matches[0]
    expires_at = now + timedelta(minutes=10)
    row = StationAppFuelingSession(
        public_id=str(uuid4()),
        idempotency_key=scoped_key,
        employee_id=g.employee.id,
        company_id=station.company_id,
        station_id=station.id,
        shift_id=shift.id,
        pump_id=pump.id,
        nozzle_id=nozzle.id,
        qr_resolution_id=resolution.id,
        requested_amount=amount,
        fueling_mode=fueling_mode,
        unit_price=nozzle.unit_price,
        fuel_code=nozzle.fuel_code,
        status="AUTHORIZATION_QUEUED",
        expires_at=expires_at,
    )
    g.db.add(row)
    semantic = {
        "fueling_session_id": row.public_id,
        "customer_id": f"station-employee:{g.employee.public_id}",
        "company_id": station.company_id,
        "station_id": station.id,
        "pump_id": pump.pump_id,
        "nozzle_id": nozzle.nozzle_id,
        "pump_address": str(configured.get("address")),
        "requested_amount": format(amount, ".2f"),
        "unit_price": format(Decimal(str(nozzle.unit_price)), ".3f"),
        "fuel_code": nozzle.fuel_code,
        "currency": "SAR",
        "protocol_code": bus.protocol_code,
        "protocol_version": bus.protocol_version,
        "protocol_hash": bus.protocol_hash,
        "expires_at": expires_at.isoformat(),
        "idempotency_key": f"station-app:{row.public_id}",
        "correlation_id": str(uuid4()),
        "session_status": "AUTHORIZATION_QUEUED",
    }
    try:
        g.db.flush()
        signer = ConfigurationSigningService(
            current_app.config["CONFIG_SIGNING_PRIVATE_KEY_FILE"],
            current_app.config["CONFIG_SIGNING_PUBLIC_KEY_FILE"],
            current_app.config["CONFIG_SIGNING_KEY_ID"],
        )
        delivery = HardwareActivationService(g.db, signer).create_customer_fueling(
            bus, "AUTHORIZE_FUELING_PRESET", semantic
        )
        row.delivery_id = delivery.delivery_id
        row.authorized_at = now
        resolution.consumed_at = now
        _audit(
            "FUELING_AUTHORIZATION_CREATED",
            fueling=row,
            details={"delivery_id": delivery.delivery_id},
        )
        g.db.commit()
        return jsonify(session=_fueling_json(row)), 201
    except IntegrityError:
        g.db.rollback()
        return _json_error("NOZZLE_BUSY", 409)
    except ContractControlError as exc:
        g.db.rollback()
        return _json_error("AUTHORIZATION_NOT_CREATED", 409, detail=str(exc)[:160])


@api.get("/api/v1/fueling-sessions/<session_id>")
@employee_required
def get_fueling(session_id):
    row = _employee_fueling(session_id)
    if row is None:
        return _json_error("FUELING_SESSION_NOT_FOUND", 404)
    _reconcile(row)
    g.db.commit()
    return jsonify(session=_fueling_json(row))


@api.post("/api/v1/fueling-sessions/<session_id>/cancel")
@employee_required
def cancel_fueling(session_id):
    row = _employee_fueling(session_id, lock=True)
    if row is None:
        return _json_error("FUELING_SESSION_NOT_FOUND", 404)
    _reconcile(row)
    if row.status == "CANCELLED":
        g.db.commit()
        return jsonify(session=_fueling_json(row))
    if row.status == "CANCELLATION_QUEUED":
        g.db.commit()
        return jsonify(session=_fueling_json(row)), 202
    if row.sale_transaction_id is not None or row.status in {
        "FUELING",
        "COMPLETED_AWAITING_PAYMENT",
        "PAID",
    }:
        g.db.rollback()
        return _json_error("ACTIVE_FUELING_CANNOT_BE_CANCELLED", 409)
    if row.status in {"FAILED", "EXPIRED"}:
        g.db.rollback()
        return _json_error("SESSION_CANNOT_BE_CANCELLED", 409)
    original = g.db.scalar(
        select(HardwareActivationDelivery).where(
            HardwareActivationDelivery.delivery_id == row.delivery_id
        )
    )
    if original is None:
        g.db.rollback()
        return _json_error("AUTHORIZATION_DELIVERY_NOT_FOUND", 409)
    bus = g.db.get(CloudBusDevice, original.device_id)
    if bus is None:
        g.db.rollback()
        return _json_error("PUMP_RUNTIME_NOT_FOUND", 409)
    now = utcnow()
    expires_at = now + timedelta(minutes=2)
    source = original.payload_json or {}
    semantic = {
        key: source.get(key)
        for key in {
            "fueling_session_id",
            "customer_id",
            "company_id",
            "station_id",
            "pump_id",
            "nozzle_id",
            "pump_address",
            "requested_amount",
            "unit_price",
            "fuel_code",
            "currency",
            "protocol_code",
            "protocol_version",
            "protocol_hash",
        }
    }
    semantic.update(
        expires_at=expires_at.isoformat(),
        idempotency_key=f"station-app-cancel:{row.public_id}:{uuid4()}",
        correlation_id=str(uuid4()),
        session_status="CANCELLED",
    )
    try:
        signer = ConfigurationSigningService(
            current_app.config["CONFIG_SIGNING_PRIVATE_KEY_FILE"],
            current_app.config["CONFIG_SIGNING_PUBLIC_KEY_FILE"],
            current_app.config["CONFIG_SIGNING_KEY_ID"],
        )
        cancellation = HardwareActivationService(
            g.db, signer
        ).create_customer_fueling(bus, "LOCK_FUELING_AUTHORIZATION", semantic)
        row.cancellation_delivery_id = cancellation.delivery_id
        row.cancel_requested_at = now
        row.status = "CANCELLATION_QUEUED"
        if original.status == "PENDING":
            original.status = "CANCELLED"
        _audit(
            "FUELING_CANCELLATION_REQUESTED",
            fueling=row,
            details={"delivery_id": cancellation.delivery_id},
        )
        g.db.commit()
        return jsonify(session=_fueling_json(row)), 202
    except (ContractControlError, IntegrityError) as exc:
        g.db.rollback()
        return _json_error("CANCELLATION_NOT_CREATED", 409, detail=str(exc)[:160])


@api.post("/api/v1/fueling-sessions/<session_id>/payment")
@employee_required
def record_payment(session_id):
    row = _employee_fueling(session_id, lock=True)
    if row is None:
        return _json_error("FUELING_SESSION_NOT_FOUND", 404)
    _reconcile(row)
    if row.status == "PAID":
        return jsonify(session=_fueling_json(row))
    if row.status != "COMPLETED_AWAITING_PAYMENT":
        return _json_error("FUELING_NOT_COMPLETED", 409)
    data = request.get_json(silent=True) or {}
    method = str(data.get("paymentMethod") or "").lower()
    reason = str(data.get("otherReason") or "").strip()
    if method not in PAYMENT_METHODS:
        return _json_error("INVALID_PAYMENT_METHOD", 400)
    if method == "other" and not 3 <= len(reason) <= 300:
        return _json_error("OTHER_PAYMENT_REASON_REQUIRED", 400)
    row.payment_method = method
    row.payment_other_reason = reason if method == "other" else None
    row.payment_recorded_at = utcnow()
    row.status = "PAID"
    _audit(
        "PAYMENT_RECORDED",
        fueling=row,
        details={"payment_method": method, "other_reason": row.payment_other_reason},
    )
    g.db.commit()
    return jsonify(session=_fueling_json(row))


@api.get("/api/v1/sales")
@employee_required
def my_sales():
    raw_date = request.args.get("date") or datetime.now(
        ZoneInfo("Asia/Riyadh")
    ).date().isoformat()
    try:
        selected_date = date.fromisoformat(raw_date)
    except ValueError:
        return _json_error("INVALID_SALES_DATE", 400)
    if selected_date > datetime.now(ZoneInfo("Asia/Riyadh")).date():
        return _json_error("FUTURE_SALES_DATE", 400)
    local_zone = ZoneInfo("Asia/Riyadh")
    start = datetime.combine(
        selected_date, datetime_time.min, tzinfo=local_zone
    ).astimezone(timezone.utc)
    end = start + timedelta(days=1)
    rows = g.db.scalars(
        select(StationAppFuelingSession)
        .where(
            StationAppFuelingSession.employee_id == g.employee.id,
            StationAppFuelingSession.sale_transaction_id.is_not(None),
            StationAppFuelingSession.status == "PAID",
            StationAppFuelingSession.completed_at >= start,
            StationAppFuelingSession.completed_at < end,
        )
        .order_by(StationAppFuelingSession.created_at.desc())
    ).all()
    return jsonify(
        date=selected_date.isoformat(),
        summary={
            "transactions": len(rows),
            "amount": round(sum(float(row.actual_amount or 0) for row in rows), 2),
            "liters": round(sum(float(row.actual_liters or 0) for row in rows), 3),
            "cash": round(
                sum(
                    float(row.actual_amount or 0)
                    for row in rows
                    if row.payment_method == "cash"
                ),
                2,
            ),
            "network": round(
                sum(
                    float(row.actual_amount or 0)
                    for row in rows
                    if row.payment_method == "network"
                ),
                2,
            ),
            "other": round(
                sum(
                    float(row.actual_amount or 0)
                    for row in rows
                    if row.payment_method == "other"
                ),
                2,
            ),
        },
        sales=[_fueling_json(row) for row in rows],
    )


@api.get("/internal/v1/employees")
@internal_required
def internal_employees():
    station_id = request.args.get("station_id", type=int)
    if not station_id:
        return _json_error("STATION_ID_REQUIRED", 400)
    employees = g.db.scalars(
        select(StationAppEmployee)
        .where(StationAppEmployee.station_id == station_id)
        .order_by(StationAppEmployee.created_at.desc())
    ).all()
    return jsonify(
        employees=[
            {
                **_employee_json(employee),
                "lastLoginAt": employee.last_login_at.isoformat()
                if employee.last_login_at
                else None,
                "createdAt": employee.created_at.isoformat(),
            }
            for employee in employees
        ]
    )


@api.post("/internal/v1/employees")
@internal_required
def internal_create_employee():
    data = request.get_json(silent=True) or {}
    name = " ".join(str(data.get("name") or "").split())
    password = str(data.get("password") or "")
    station_id = data.get("stationId")
    if not name or len(name) > 160:
        return _json_error("INVALID_EMPLOYEE_NAME", 400)
    if not 6 <= len(password) <= 128:
        return _json_error("PASSWORD_LENGTH_INVALID", 400)
    station = g.db.get(Station, int(station_id)) if str(station_id).isdigit() else None
    if station is None or station.deleted_at is not None:
        return _json_error("STATION_NOT_FOUND", 404)
    employee = StationAppEmployee(
        public_id=str(uuid4()),
        company_id=station.company_id,
        station_id=station.id,
        name=name,
        password_lookup_digest=password_lookup_digest(password),
        password_hash=password_hash(password),
        enabled=True,
        created_by_user_id=data.get("createdByUserId"),
    )
    g.db.add(employee)
    try:
        g.db.commit()
    except IntegrityError:
        g.db.rollback()
        return _json_error("PASSWORD_ALREADY_ASSIGNED", 409)
    return jsonify(employee=_employee_json(employee, station)), 201


@api.patch("/internal/v1/employees/<public_id>")
@internal_required
def internal_update_employee(public_id):
    employee = g.db.scalar(
        select(StationAppEmployee).where(StationAppEmployee.public_id == public_id)
    )
    if employee is None:
        return _json_error("EMPLOYEE_NOT_FOUND", 404)
    data = request.get_json(silent=True) or {}
    if "enabled" in data:
        employee.enabled = bool(data["enabled"])
        if not employee.enabled:
            now = utcnow()
            sessions = g.db.scalars(
                select(StationAppSession).where(
                    StationAppSession.employee_id == employee.id,
                    StationAppSession.revoked_at.is_(None),
                    StationAppSession.expires_at > now,
                )
            ).all()
            for session_row in sessions:
                session_row.revoked_at = now
                session_row.revoke_reason = "EMPLOYEE_DISABLED"
    g.db.commit()
    return jsonify(employee=_employee_json(employee))


@api.get("/internal/v1/employee-sales")
@internal_required
def internal_employee_sales():
    station_id = request.args.get("station_id", type=int)
    if not station_id:
        return _json_error("STATION_ID_REQUIRED", 400)
    rows = g.db.execute(
        select(StationAppFuelingSession, StationAppEmployee)
        .join(
            StationAppEmployee,
            StationAppEmployee.id == StationAppFuelingSession.employee_id,
        )
        .where(
            StationAppFuelingSession.station_id == station_id,
            StationAppFuelingSession.sale_transaction_id.is_not(None),
        )
        .order_by(StationAppFuelingSession.created_at.desc())
        .limit(500)
    ).all()
    totals = {}
    recent = []
    for sale, employee in rows:
        item = totals.setdefault(
            employee.public_id,
            {
                "employeeId": employee.public_id,
                "employeeName": employee.name,
                "count": 0,
                "amount": 0.0,
                "liters": 0.0,
                "cash": 0.0,
                "network": 0.0,
                "other": 0.0,
            },
        )
        amount = float(sale.actual_amount or 0)
        item["count"] += 1
        item["amount"] += amount
        item["liters"] += float(sale.actual_liters or 0)
        if sale.payment_method in {"cash", "network", "other"}:
            item[sale.payment_method] += amount
        recent.append({"employeeName": employee.name, **_fueling_json(sale)})
    return jsonify(totals=list(totals.values()), recent=recent[:100])


def _employee_fueling(session_id, lock=False):
    statement = select(StationAppFuelingSession).where(
        StationAppFuelingSession.public_id == session_id,
        StationAppFuelingSession.employee_id == g.employee.id,
    )
    if lock:
        statement = statement.with_for_update()
    return g.db.scalar(statement)


def _reconcile(row):
    if row.status in {"PAID", "FAILED", "EXPIRED", "CANCELLED"}:
        return
    now = utcnow()
    cancellation = (
        g.db.scalar(
            select(HardwareActivationDelivery).where(
                HardwareActivationDelivery.delivery_id
                == row.cancellation_delivery_id
            )
        )
        if row.cancellation_delivery_id
        else None
    )
    if cancellation and cancellation.status == "SUCCEEDED":
        row.status = "CANCELLED"
        row.cancelled_at = cancellation.acknowledged_at or now
        row.completed_at = row.cancelled_at
        row.failure_code = None
        row.failure_message = None
        _audit(
            "FUELING_CANCELLED",
            fueling=row,
            details={"delivery_id": cancellation.delivery_id},
        )
        return
    cancellation_pending = bool(
        cancellation
        and cancellation.status
        not in {"SUCCEEDED", "FAILED", "REJECTED"}
    )
    cancellation_failed = bool(
        cancellation and cancellation.status in {"FAILED", "REJECTED"}
    )
    if cancellation_failed:
        row.failure_code = cancellation.error_code or "CANCELLATION_FAILED"
        row.failure_message = cancellation.error_message
    delivery = (
        g.db.scalar(
            select(HardwareActivationDelivery).where(
                HardwareActivationDelivery.delivery_id == row.delivery_id
            )
        )
        if row.delivery_id
        else None
    )
    if delivery:
        status_map = {
            "RECEIVED": "EDGE_RECEIVED",
            "VERIFIED": "EDGE_RECEIVED",
            "AUTHORIZED": "PUMP_WAITING",
            "EXECUTING": "PUMP_WAITING",
            "SUCCEEDED": "PUMP_AUTHORIZED",
            "FAILED": "FAILED",
            "REJECTED": "FAILED",
        }
        row.status = status_map.get(delivery.status, row.status)
        if delivery.status in {"FAILED", "REJECTED"}:
            row.failure_code = delivery.error_code or "EDGE_COMMAND_FAILED"
            row.failure_message = delivery.error_message
            row.completed_at = now
            return
    if row.sale_transaction_id is None:
        claimed_sales = select(
            StationAppFuelingSession.sale_transaction_id
        ).where(StationAppFuelingSession.sale_transaction_id.is_not(None))
        sale = g.db.scalar(
            select(SaleTransaction)
            .where(
                SaleTransaction.station_id == row.station_id,
                SaleTransaction.pump_id == row.pump_id,
                SaleTransaction.nozzle_id == row.nozzle_id,
                SaleTransaction.started_at >= row.created_at - timedelta(minutes=2),
                SaleTransaction.id.not_in(claimed_sales),
            )
            .order_by(SaleTransaction.started_at.asc())
        )
        if sale:
            row.sale_transaction_id = sale.id
            row.fueling_started_at = sale.started_at
    else:
        sale = g.db.get(SaleTransaction, row.sale_transaction_id)
    if row.sale_transaction_id:
        sale = sale or g.db.get(SaleTransaction, row.sale_transaction_id)
        row.actual_amount = sale.amount
        row.actual_liters = sale.liters
        row.unit_price = sale.unit_price
        row.fuel_code = sale.fuel_code
        if sale.status == "completed":
            row.status = "COMPLETED_AWAITING_PAYMENT"
            row.completed_at = sale.ended_at or now
        else:
            row.status = "FUELING"
    elif cancellation_pending:
        row.status = "CANCELLATION_QUEUED"
    elif cancellation_failed:
        row.status = "CANCELLATION_FAILED"
    elif _aware(row.expires_at) <= now and row.status not in {
        "PUMP_AUTHORIZED",
        "FUELING",
    }:
        row.status = "EXPIRED"
        row.failure_code = "AUTHORIZATION_EXPIRED"


def _aware(value):
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def _dispenser_available(station, pump, nozzle):
    return bool(
        station
        and station.status == "active"
        and pump
        and pump.station_id == station.id
        and pump.enabled
        and pump.status not in {"offline", "disabled"}
        and nozzle
        and nozzle.station_id == station.id
        and nozzle.pump_id == pump.id
        and nozzle.enabled
        and nozzle.unit_price
    )


def _hardware_address(value):
    raw = str(value or "").strip().lower()
    if raw.startswith("0x"):
        raw = raw[2:]
    try:
        return format(int(raw, 16), "x")
    except (TypeError, ValueError):
        return ""


def _active_hardware_buses(station_id, edge_device_id):
    return g.db.scalars(
        select(CloudBusDevice).where(
            CloudBusDevice.station_id == station_id,
            CloudBusDevice.edge_device_id == edge_device_id,
            CloudBusDevice.device_type == "FUEL_PUMP",
            CloudBusDevice.status == "ACTIVE",
            CloudBusDevice.configuration_status == "STAGED",
            CloudBusDevice.hardware_active.is_(True),
        )
    ).all()


def _matching_hardware_targets(buses, pump, nozzle):
    pump_address = _hardware_address(pump.device_address)
    if not pump_address:
        return []
    matches = []
    for bus in buses:
        if _hardware_address(bus.device_address) != pump_address:
            continue
        for configured in (bus.protocol_config_json or {}).get("nozzles", []):
            if str(configured.get("id")) == str(nozzle.nozzle_id) and str(
                configured.get("fuel_code") or ""
            ).lower() == str(nozzle.fuel_code or "").lower():
                matches.append((bus, configured))
    return matches
