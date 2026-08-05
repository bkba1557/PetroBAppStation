from types import SimpleNamespace

from app.customer_api.fueling import (
    OPERATIONAL_EDGE_ASSIGNMENT_STATES,
    _hardware_address,
    _matching_hardware_targets,
)


def test_approved_edge_assignment_is_operational_for_customer_fueling():
    assert "APPROVED" in OPERATIONAL_EDGE_ASSIGNMENT_STATES
    assert "ACTIVE" in OPERATIONAL_EDGE_ASSIGNMENT_STATES


def test_hardware_address_normalizes_cloud_and_pump_forms():
    assert _hardware_address("0x42") == _hardware_address("42") == "42"


def test_target_match_uses_pump_address_when_nozzle_ids_repeat():
    pump = SimpleNamespace(device_address="0x42")
    nozzle = SimpleNamespace(nozzle_id="N-1", fuel_code="gasoline95")
    buses = [
        SimpleNamespace(device_address="40", protocol_config_json={"nozzles": [
            {"id": "N-1", "fuel_code": "gasoline95", "address": "0x40"}]}),
        SimpleNamespace(device_address="42", protocol_config_json={"nozzles": [
            {"id": "N-1", "fuel_code": "gasoline95", "address": "0x42"}]}),
        SimpleNamespace(device_address="44", protocol_config_json={"nozzles": [
            {"id": "N-1", "fuel_code": "diesel", "address": "0x44"}]}),
    ]
    matches = _matching_hardware_targets(buses, pump, nozzle)
    assert len(matches) == 1
    assert matches[0][0].device_address == "42"
    assert matches[0][1]["address"] == "0x42"


def test_target_match_rejects_wrong_fuel_on_same_nozzle_identity():
    pump = SimpleNamespace(device_address="0x44")
    nozzle = SimpleNamespace(nozzle_id="N-1", fuel_code="gasoline95")
    bus = SimpleNamespace(device_address="44", protocol_config_json={"nozzles": [
        {"id": "N-1", "fuel_code": "diesel", "address": "0x44"}]})
    assert _matching_hardware_targets([bus], pump, nozzle) == []

