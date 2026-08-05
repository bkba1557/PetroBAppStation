import re


_ALIASES = {
    "91": "gasoline91",
    "gasoline91": "gasoline91",
    "petrol91": "gasoline91",
    "95": "gasoline95",
    "gasoline95": "gasoline95",
    "petrol95": "gasoline95",
    "diesel": "diesel",
    "kerosene": "kerosene",
    "lpg": "lpg",
}


def normalize_fuel_code(value: object) -> str:
    """Return the canonical customer-facing code without inventing products."""
    raw = str(value or "").strip().lower()
    compact = re.sub(r"[^a-z0-9]", "", raw)
    if compact in _ALIASES:
        return _ALIASES[compact]
    return re.sub(r"[^a-z0-9]+", "_", raw).strip("_") or "other"


def public_fuel_kind(code: object) -> str:
    canonical = normalize_fuel_code(code)
    if canonical in {"gasoline91", "gasoline95", "diesel", "kerosene", "lpg"}:
        return canonical
    return "other"


def availability_reason(
    *,
    company_enabled: bool,
    station_enabled: bool,
    status: str,
    scheduled: bool,
    edge_online: bool,
    has_prices: bool,
    has_compatible_nozzles: bool,
    hardware_enabled: bool,
) -> str:
    normalized_status = str(status or "DISABLED").upper()
    if not company_enabled:
        return "COMPANY_SELF_SERVICE_DISABLED"
    if not station_enabled:
        return "STATION_SELF_SERVICE_DISABLED"
    if normalized_status == "MAINTENANCE":
        return "STATION_MAINTENANCE"
    if normalized_status not in {"ACTIVE", "ENABLED", "PILOT", "SCHEDULED"}:
        return "STATION_SELF_SERVICE_DISABLED"
    if not scheduled:
        return "SELF_SERVICE_OUTSIDE_SCHEDULE"
    if not edge_online:
        return "EDGE_OFFLINE"
    if not has_prices:
        return "FUEL_PRICE_UNAVAILABLE"
    if not has_compatible_nozzles:
        return "NO_COMPATIBLE_NOZZLE"
    if not hardware_enabled:
        return "HARDWARE_FUELING_DISABLED"
    return "AVAILABLE"

