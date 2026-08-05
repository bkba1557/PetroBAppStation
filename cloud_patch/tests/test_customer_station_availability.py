import pytest

from app.customer_api.fuel_codes import availability_reason, normalize_fuel_code


@pytest.mark.parametrize(
    ("raw", "canonical"),
    [
        ("gasoline91", "gasoline91"),
        ("gasoline_91", "gasoline91"),
        ("GASOLINE_91", "gasoline91"),
        ("91", "gasoline91"),
        ("gasoline95", "gasoline95"),
        ("gasoline_95", "gasoline95"),
        ("GASOLINE_95", "gasoline95"),
        ("95", "gasoline95"),
        ("98", "gasoline98"),
        ("GASOLINE_98", "gasoline98"),
        ("DIESEL", "diesel"),
        ("Kerosene", "kerosene"),
        ("LPG", "lpg"),
        ("bio-fuel", "bio_fuel"),
    ],
)
def test_normalize_fuel_code(raw, canonical):
    assert normalize_fuel_code(raw) == canonical


def _reason(**overrides):
    values = {
        "company_enabled": True,
        "station_enabled": True,
        "status": "PILOT",
        "scheduled": True,
        "edge_online": True,
        "has_prices": True,
        "has_compatible_nozzles": True,
        "hardware_enabled": False,
    }
    values.update(overrides)
    return availability_reason(**values)


def test_hardware_disabled_only_blocks_authorization():
    assert _reason() == "HARDWARE_FUELING_DISABLED"


def test_company_disabled_reason():
    assert _reason(company_enabled=False) == "COMPANY_SELF_SERVICE_DISABLED"


def test_station_disabled_reason():
    assert _reason(station_enabled=False) == "STATION_SELF_SERVICE_DISABLED"


def test_maintenance_reason():
    assert _reason(status="MAINTENANCE") == "STATION_MAINTENANCE"


def test_edge_offline_reason():
    assert _reason(edge_online=False) == "EDGE_OFFLINE"


def test_missing_price_reason():
    assert _reason(has_prices=False) == "FUEL_PRICE_UNAVAILABLE"


def test_no_compatible_nozzle_reason():
    assert _reason(has_compatible_nozzles=False) == "NO_COMPATIBLE_NOZZLE"


def test_active_station_with_hardware_is_available():
    assert _reason(status="ACTIVE", hardware_enabled=True) == "AVAILABLE"
