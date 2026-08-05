import base64
import hashlib
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from sqlalchemy import select

from app.edge_contracts.sync import ContractSyncAgent, HardwareCommandSyncAgent
from app.enrollment_agent.identity import LocalIdentity
from app.enrollment_agent.security import canonical_json
from database.base import Base
from database.models import (
    ContractDeliveryState,
    EdgeContract,
    EdgeProtocolVersion,
    HardwareCommandInbox,
    SerialPort,
    StagedDeviceConfiguration,
    TrustedCloudSigningKey,
)
from database.session import Database


def b64(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode().rstrip("=")


@pytest.fixture()
def sync_setup(tmp_path: Path):
    db_path = tmp_path / "contract.db"
    database = Database(f"sqlite+pysqlite:///{db_path}")
    Base.metadata.create_all(database.engine)
    cloud_key = Ed25519PrivateKey.generate()
    cloud_public = cloud_key.public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw
    )
    cloud_fingerprint = hashlib.sha256(cloud_public).hexdigest()
    identity = LocalIdentity("edge-contract-fixture", "test", "edge-fingerprint")
    with database.session_factory() as session:
        session.add(TrustedCloudSigningKey(
            key_id="nnexoris-config-signing-2026-01",
            algorithm="Ed25519",
            public_key_encoded=b64(cloud_public),
            fingerprint_sha256=cloud_fingerprint,
            status="ACTIVE",
                received_via="TEST",
        ))
        session.commit()
    definition = {
        "schema_version": "1.0",
        "contract_code": "NXS-EC-000001",
        "version": 1,
        "edge_device_uuid": identity.device_uuid,
        "edge_public_fingerprint": identity.public_key_fingerprint,
        "company_id": 1,
        "station_id": 1,
        "hardware_policy": {
            "activation_policy": "MANUAL_ONLY",
            "allowed_device_types": ["TANK_GAUGE"],
        },
        "port_policy": {
            "mode": "SELECTED_PORTS_ONLY",
            "ports": [{
                "stable_identity": "by-id:BG03WKJ0",
                "allowed_device_types": ["TANK_GAUGE"],
            }],
        },
        "protocol_policy": {
            "mode": "SELECTED_PROTOCOLS_ONLY",
            "protocol_codes": ["DOVER_STARTA_ITALIANA"],
        },
        "offline_policy": {"allow_offline_operation": True},
        "persistent_autostart_policy": {"allow_persistent_autostart": True},
        "command_policy": {
            "allowed_command_classes": ["READ_ONLY", "RUNTIME_CONTROL"]
        },
        "sync_policy": {"telemetry_sync_enabled": True},
        "issued_at": datetime.now(UTC).isoformat(),
        "effective_at": datetime.now(UTC).isoformat(),
        "expires_at": None,
    }
    definition_hash = hashlib.sha256(canonical_json(definition)).hexdigest()
    envelope = {
        "contract_code": "NXS-EC-000001",
        "version": 1,
        "definition_hash": definition_hash,
        "definition": definition,
        "issued_at": definition["issued_at"],
        "signing_key_id": "nnexoris-config-signing-2026-01",
    }
    package = {
        "delivery_id": "contract-delivery-1",
        "contract_id": 1,
        "contract_version_id": 11,
        "definition_json": definition,
        "definition_hash": definition_hash,
        "envelope": envelope,
        "signature": b64(cloud_key.sign(canonical_json(envelope))),
        "signature_algorithm": "Ed25519",
        "signing_key_id": "nnexoris-config-signing-2026-01",
    }
    return database, identity, cloud_key, cloud_fingerprint, package


@pytest.mark.asyncio
async def test_contract_sync_persists_active_and_retries_ack(sync_setup):
    database, identity, _, fingerprint, package = sync_setup

    class Client:
        async def pull_contracts(self, _payload):
            return {"items": [package]}

        async def acknowledge_contract(self, delivery_id, payload):
            assert delivery_id == "contract-delivery-1"
            assert payload["status"] == "ACTIVE"
            return {"accepted": True}

    await ContractSyncAgent(database, identity, Client(), fingerprint).sync_once()
    with database.session_factory() as session:
        assert session.scalar(select(EdgeContract)).status == "ACTIVE"
        delivery = session.scalar(select(ContractDeliveryState))
        assert delivery.status == "ACTIVE"
        assert delivery.acknowledged_at is not None


@pytest.mark.asyncio
async def test_hardware_command_is_durable_and_stops_at_authorized(sync_setup):
    database, identity, cloud_key, fingerprint, package = sync_setup

    class ContractClient:
        async def pull_contracts(self, _payload):
            return {"items": [package]}

        async def acknowledge_contract(self, _delivery_id, _payload):
            return {"accepted": True}

    await ContractSyncAgent(
        database, identity, ContractClient(), fingerprint
    ).sync_once()
    now = datetime.now(UTC)
    with database.session_factory() as session:
        session.add(SerialPort(
            edge_device_id=identity.device_uuid,
            stable_identity="by-id:BG03WKJ0",
            serial_number="BG03WKJ0",
            status="AVAILABLE",
            ownership_status="FREE",
        ))
        session.add(EdgeProtocolVersion(
            cloud_protocol_version_id=5,
            protocol_code="DOVER_STARTA_ITALIANA",
            protocol_version="1.0-authoring.1",
            schema_version="1.0",
            definition_json={},
            definition_hash="0" * 64,
            signed_envelope_json={},
            signature="fixture",
            signature_algorithm="Ed25519",
            signing_key_id="nnexoris-config-signing-2026-01",
            status="VERIFIED",
        ))
        session.add(StagedDeviceConfiguration(
            cloud_device_id="tank-device-50175",
            configuration_version_id="config-1",
            serial_port_identity="by-id:BG03WKJ0",
            device_type="TANK_GAUGE",
            device_name="Tank - 1",
            protocol_code="DOVER_STARTA_ITALIANA",
            device_address="50175",
            status="STAGED",
        ))
        session.commit()
    payload = {
        "action": "ACTIVATE_DEVICE_RUNTIME",
        "edge_device_uuid": identity.device_uuid,
        "device_uuid": "tank-device-50175",
        "tank_id": "tank-1",
        "configuration_version_id": "config-1",
        "contract_version_id": 11,
        "stable_port_identity": "by-id:BG03WKJ0",
        "protocol_code": "DOVER_STARTA_ITALIANA",
        "protocol_version": "1.0-authoring.1",
        "protocol_hash": "0" * 64,
        "probe_serial": "50175",
        "allowed_capabilities": ["READ_PROBE_MEASUREMENT"],
        "issued_at": now.isoformat(),
        "expires_at": (now + timedelta(minutes=10)).isoformat(),
        "request_id": str(uuid4()),
    }
    payload_hash = hashlib.sha256(canonical_json(payload)).hexdigest()
    envelope = {
        "delivery_id": "hardware-delivery-1",
        "payload_hash": payload_hash,
        "payload": payload,
        "signing_key_id": "nnexoris-config-signing-2026-01",
    }
    item = {
        "delivery_id": "hardware-delivery-1",
        "payload": payload,
        "payload_hash": payload_hash,
        "envelope": envelope,
        "signature": b64(cloud_key.sign(canonical_json(envelope))),
        "signature_algorithm": "Ed25519",
        "signing_key_id": "nnexoris-config-signing-2026-01",
    }

    class HardwareClient:
        async def pull_hardware_commands(self, _payload):
            return {"items": [item]}

        async def acknowledge_hardware_command(self, _delivery_id, ack):
            assert ack["status"] == "AUTHORIZED"
            return {"accepted": True}

    await HardwareCommandSyncAgent(database, identity, HardwareClient()).sync_once()
    with database.session_factory() as session:
        command = session.scalar(select(HardwareCommandInbox))
        assert command.status == "AUTHORIZED"
        assert command.executed_at is None


@pytest.mark.asyncio
async def test_succeeded_delivery_is_reacknowledged_without_reexecution(sync_setup):
    database, identity, _, _, _ = sync_setup
    with database.session_factory() as session:
        session.add(HardwareCommandInbox(
            delivery_id="already-succeeded",
            command_id="already-succeeded",
            action="AUTHORIZE_FUELING_PRESET",
            cloud_device_id="pump-1",
            contract_version_id=1,
            configuration_version_id="1",
            payload_hash="0" * 64,
            signed_envelope_json={},
            signature="fixture",
            signing_key_id="fixture",
            status="SUCCEEDED",
            executed_at=datetime.now(UTC),
        ))
        session.commit()

    class Client:
        acknowledgements = []

        async def pull_hardware_commands(self, _payload):
            return {"items": [{"delivery_id": "already-succeeded"}]}

        async def acknowledge_hardware_command(self, delivery_id, ack):
            self.acknowledgements.append((delivery_id, ack))

    client = Client()
    await HardwareCommandSyncAgent(database, identity, client).sync_once()
    assert client.acknowledgements == [
        ("already-succeeded", {"status": "SUCCEEDED"})
    ]


@pytest.mark.asyncio
async def test_executing_delivery_after_restart_is_never_replayed(sync_setup):
    database, identity, _, _, _ = sync_setup
    with database.session_factory() as session:
        session.add(HardwareCommandInbox(
            delivery_id="execution-unknown",
            command_id="execution-unknown",
            action="AUTHORIZE_FUELING_PRESET",
            cloud_device_id="pump-1",
            contract_version_id=1,
            configuration_version_id="1",
            payload_hash="0" * 64,
            signed_envelope_json={"payload": {}},
            signature="fixture",
            signing_key_id="fixture",
            status="EXECUTING",
        ))
        session.commit()

    class Manager:
        enabled = True
        calls = 0

        async def authorize_fueling_preset(self, _payload):
            self.calls += 1

    class Client:
        acknowledgements = []

        async def acknowledge_hardware_command(self, delivery_id, ack):
            self.acknowledgements.append((delivery_id, ack))

    manager = Manager()
    client = Client()
    agent = HardwareCommandSyncAgent(
        database, identity, client, pump_runtime_manager=manager
    )
    await agent.resume_authorized()
    assert manager.calls == 0
    assert client.acknowledgements == [(
        "execution-unknown",
        {
            "status": "FAILED",
            "error_code": "EXECUTION_RESULT_UNKNOWN_NO_REPLAY",
        },
    )]
    with database.session_factory() as session:
        row = session.scalar(select(HardwareCommandInbox))
        assert row.status == "FAILED"
        assert row.failure_code == "EXECUTION_RESULT_UNKNOWN_NO_REPLAY"
