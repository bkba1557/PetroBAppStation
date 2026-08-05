from flask import current_app, jsonify
from sqlalchemy import select

from app.extensions import get_session
from app.models import Company, EdgeDevice, FuelPrice, Location, Nozzle, Pump, Station, utcnow

from . import customer_api
from .common import api_error
from .fuel_codes import availability_reason, normalize_fuel_code, public_fuel_kind
from .security import customer_required


def _scheduled(station, now):
    return (
        (station.self_service_start_at is None or station.self_service_start_at <= now)
        and (station.self_service_end_at is None or station.self_service_end_at >= now)
    )


def _prices(db, station):
    """Latest effective active price per canonical code, independent of hardware."""
    now = utcnow()
    rows = db.scalars(
        select(FuelPrice)
        .where(
            FuelPrice.station_id == station.id,
            FuelPrice.active.is_(True),
            FuelPrice.effective_at <= now,
        )
        .order_by(FuelPrice.effective_at.desc(), FuelPrice.id.desc())
    ).all()
    allowed = {normalize_fuel_code(code) for code in (station.allowed_fuel_types or [])}
    latest = {}
    for row in rows:
        canonical = normalize_fuel_code(row.fuel_code)
        if allowed and canonical not in allowed:
            continue
        latest.setdefault(canonical, row)
    return [(code, latest[code]) for code in sorted(latest)]


def _price_json(code, row):
    name_ar = row.fuel_name_ar or row.fuel_name_en or code
    name_en = row.fuel_name_en or row.fuel_name_ar or code
    return {
        "product": {
            "id": code,
            "code": code,
            "rawCode": row.fuel_code,
            "kind": public_fuel_kind(code),
            "name": name_ar,
            "nameAr": name_ar,
            "nameEn": name_en,
        },
        "unitPrice": float(row.price),
        "currency": row.currency,
        "effectiveAt": row.effective_at.isoformat(),
    }


def _availability(db, station, company, prices=None):
    now = utcnow()
    scheduled = _scheduled(station, now)
    normalized_status = str(station.self_service_status or "DISABLED").upper()
    public_status = "ACTIVE" if normalized_status == "ENABLED" else normalized_status
    company_enabled = bool(company and company.customer_self_service_enabled)
    station_enabled = bool(station.customer_self_service_enabled)
    self_service = bool(
        company_enabled
        and station_enabled
        and normalized_status in {"ACTIVE", "ENABLED", "PILOT", "SCHEDULED"}
        and scheduled
    )
    hardware_enabled = bool(current_app.config["CUSTOMER_HARDWARE_FUELING_ENABLED"])
    edge = db.scalar(
        select(EdgeDevice)
        .where(EdgeDevice.station_id == station.id, EdgeDevice.deleted_at.is_(None))
        .order_by(EdgeDevice.id.desc())
    )
    edge_online = bool(
        edge and edge.status == "ACTIVE" and edge.connectivity_status == "ONLINE"
    )
    price_rows = prices if prices is not None else _prices(db, station)
    priced_codes = {code for code, _ in price_rows}
    allowed = {normalize_fuel_code(code) for code in (station.allowed_fuel_types or [])}
    nozzles = db.scalars(
        select(Nozzle).where(
            Nozzle.station_id == station.id,
            Nozzle.enabled.is_(True),
            Nozzle.deleted_at.is_(None),
        )
    ).all()
    compatible = [
        nozzle
        for nozzle in nozzles
        if normalize_fuel_code(nozzle.fuel_code) in priced_codes
        and (not allowed or normalize_fuel_code(nozzle.fuel_code) in allowed)
    ]
    reason = availability_reason(
        company_enabled=company_enabled,
        station_enabled=station_enabled,
        status=normalized_status,
        scheduled=scheduled,
        edge_online=edge_online,
        has_prices=bool(price_rows),
        has_compatible_nozzles=bool(compatible),
        hardware_enabled=hardware_enabled,
    )
    return {
        "stationVisible": True,
        "companySelfServiceEnabled": company_enabled,
        "stationSelfServiceEnabled": station_enabled,
        "selfServiceEnabled": self_service,
        "hardwareFuelingEnabled": hardware_enabled,
        "edgeOnline": edge_online,
        "availabilityStatus": public_status,
        "availabilityReason": reason,
        "appFuelingAvailable": reason == "AVAILABLE",
        "pilotOperatorSupervised": public_status == "PILOT"
        or not current_app.config.get("ACTIVE_FUELING_STOP_PROVEN", False),
    }


def _station_json(db, station):
    company = db.get(Company, station.company_id)
    location = db.scalar(
        select(Location).where(
            Location.entity_type == "station",
            Location.entity_id == station.id,
            Location.deleted_at.is_(None),
            Location.status == "active",
        )
    )
    address = (location.formatted_address if location else None) or station.address or ""
    prices = _prices(db, station)
    availability = _availability(db, station, company, prices)
    return {
        "id": station.station_id,
        "name": station.name_ar or station.name_en,
        "logoUrl": station.logo,
        "location": {
            "latitude": float(location.latitude)
            if location and location.latitude is not None
            else 0.0,
            "longitude": float(location.longitude)
            if location and location.longitude is not None
            else 0.0,
            "address": address,
        },
        "operatingStatus": "open"
        if station.status == "active"
        else "temporarilyUnavailable",
        "fuelPrices": [_price_json(code, row) for code, row in prices],
        "fuelTypes": [_price_json(code, row) for code, row in prices],
        "services": [],
        "selfServiceAvailable": availability["selfServiceEnabled"],
        "selfServiceStatus": availability["availabilityStatus"],
        "operatingHours": None,
        **availability,
    }


def _visible_station_query():
    return (
        select(Station)
        .join(Company, Company.id == Station.company_id)
        .where(
            Company.enabled.is_(True),
            Company.lifecycle_status == "ACTIVE",
            Company.deleted_at.is_(None),
            Station.status == "active",
            Station.deleted_at.is_(None),
        )
    )


def _station(db, station_id):
    return db.scalar(_visible_station_query().where(Station.station_id == station_id))


@customer_api.get("/stations")
@customer_required
def stations_list():
    db = get_session()
    rows = db.scalars(_visible_station_query().order_by(Station.id)).all()
    return jsonify([_station_json(db, row) for row in rows])


@customer_api.get("/stations/<station_id>")
@customer_required
def station_detail(station_id):
    db = get_session()
    station = _station(db, station_id)
    if station is None:
        return api_error("STATION_NOT_FOUND", 404)
    from .common import audit

    audit(
        "STATION_VIEWED",
        entity_type="station",
        entity_id=station.station_id,
        company_id=station.company_id,
        station_id=station.id,
    )
    db.commit()
    return jsonify(_station_json(db, station))


@customer_api.get("/stations/<station_id>/prices")
@customer_api.get("/stations/<station_id>/fuel-prices")
@customer_required
def station_prices(station_id):
    db = get_session()
    station = _station(db, station_id)
    if station is None:
        return api_error("STATION_NOT_FOUND", 404)
    return jsonify([_price_json(code, row) for code, row in _prices(db, station)])


@customer_api.get("/stations/<station_id>/availability")
@customer_required
def station_availability(station_id):
    db = get_session()
    station = _station(db, station_id)
    if station is None:
        return api_error("STATION_NOT_FOUND", 404)
    company = db.get(Company, station.company_id)
    prices = _prices(db, station)
    pumps = db.scalars(
        select(Pump).where(
            Pump.station_id == station.id,
            Pump.enabled.is_(True),
            Pump.deleted_at.is_(None),
        )
    ).all()
    nozzles = db.scalars(
        select(Nozzle).where(
            Nozzle.station_id == station.id,
            Nozzle.enabled.is_(True),
            Nozzle.deleted_at.is_(None),
        )
    ).all()
    return jsonify(
        {
            "stationId": station.station_id,
            "fuelTypes": [_price_json(code, row) for code, row in prices],
            **_availability(db, station, company, prices),
            "pumps": [
                {
                    "id": pump.pump_id,
                    "number": pump.pump_number,
                    "status": pump.status,
                    "available": bool(
                        pump.enabled and pump.status.lower() not in {"offline", "disabled"}
                    ),
                    "nozzles": [
                        {
                            "id": nozzle.nozzle_id,
                            "number": nozzle.nozzle_number,
                            "fuelProductId": normalize_fuel_code(nozzle.fuel_code),
                            "rawFuelCode": nozzle.fuel_code,
                            "unitPrice": float(nozzle.unit_price or 0),
                            "status": nozzle.status,
                        }
                        for nozzle in nozzles
                        if nozzle.pump_id == pump.id
                    ],
                }
                for pump in pumps
            ],
        }
    )

