"""Outbound-only persistent Edge contract and semantic hardware-command sync."""

from __future__ import annotations

import hashlib
import os
import secrets
from decimal import Decimal, InvalidOperation
from datetime import UTC, datetime
from uuid import uuid4

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.edge_contracts.service import (
    ContractAuthorizationService,
    EdgeContractError,
    EdgeContractVerifier,
)
from app.enrollment_agent.cloud_control import CloudControlPlaneClient
from app.enrollment_agent.identity import LocalIdentity
from app.enrollment_agent.security import canonical_json, unb64
from app.shared.time import utcnow
from app.tank_runtime.production import ProductionTankRuntimeManager
from app.pump_runtime.bridge import _address
from app.pump_runtime.bridge import ProductionPumpRuntimeManager
from app.priceboard_runtime.production import ProductionPriceBoardRuntimeManager
from database.models import (
    ContractDeliveryState,
    EdgeContract,
    EdgeContractVersion,
    EdgeProtocolVersion,
    HardwareCommandInbox,
    SerialPort,
    StagedDeviceConfiguration,
    TrustedCloudSigningKey,
)
from database.session import Database


class ContractSyncAgent:
    def __init__(
        self,
        database: Database,
        identity: LocalIdentity,
        client: CloudControlPlaneClient,
        expected_cloud_key_fingerprint: str,
    ) -> None:
        self.database = database
        self.identity = identity
        self.client = client
        self.verifier = EdgeContractVerifier(
            identity.device_uuid,
            expected_cloud_key_fingerprint,
            identity.public_key_fingerprint,
        )

    def _installed(self) -> dict[str, object]:
        with self.database.session_factory() as session:
            contract = session.scalar(select(EdgeContract).where(EdgeContract.status == "ACTIVE"))
            version = (
                session.get(EdgeContractVersion, contract.active_version_id)
                if contract and contract.active_version_id
                else None
            )
            return {
                "installed_contract_code": contract.contract_code if contract else None,
                "installed_contract_version": version.contract_version if version else None,
                "installed_contract_hash": version.definition_hash if version else None,
            }

    def _persist(self, package: dict[str, object], delivery_id: str) -> ContractDeliveryState:
        with self.database.session_factory() as session:
            state = session.scalar(
                select(ContractDeliveryState).where(
                    ContractDeliveryState.delivery_id == delivery_id
                )
            )
            if state is not None:
                return state
            verified = self.verifier.verify(session, package)
            contract = session.scalar(
                select(EdgeContract).where(
                    EdgeContract.cloud_contract_id == verified.cloud_contract_id
                )
            )
            if contract is None:
                contract = EdgeContract(
                    contract_code=verified.contract_code,
                    edge_device_uuid=self.identity.device_uuid,
                    cloud_contract_id=verified.cloud_contract_id,
                    status="PENDING",
                )
                session.add(contract)
                session.flush()
            version = session.scalar(
                select(EdgeContractVersion).where(
                    EdgeContractVersion.cloud_contract_version_id == verified.cloud_version_id
                )
            )
            if version is None:
                version = EdgeContractVersion(
                    cloud_contract_version_id=verified.cloud_version_id,
                    contract_id=contract.id,
                    contract_code=verified.contract_code,
                    contract_version=verified.version,
                    definition_json=verified.definition,
                    definition_hash=verified.definition_hash,
                    signed_envelope_json=verified.envelope,
                    signature=verified.signature,
                    signature_algorithm="Ed25519",
                    signing_key_id=verified.signing_key_id,
                    status="ACTIVE",
                    downloaded_at=utcnow(),
                    verified_at=utcnow(),
                    activated_at=utcnow(),
                )
                session.add(version)
                session.flush()
            previous = (
                session.get(EdgeContractVersion, contract.active_version_id)
                if contract.active_version_id
                else None
            )
            if previous and previous.id != version.id:
                previous.status = "SUPERSEDED"
                previous.superseded_at = utcnow()
            version.status = "ACTIVE"
            contract.active_version_id = version.id
            contract.status = "ACTIVE"
            state = ContractDeliveryState(
                delivery_id=delivery_id,
                cloud_contract_version_id=verified.cloud_version_id,
                status="ACTIVE",
                request_id=str(uuid4()),
                received_at=utcnow(),
                next_attempt_at=utcnow(),
            )
            session.add(state)
            session.commit()
            return state

    async def sync_once(self) -> dict[str, object]:
        fallback_request = getattr(self.client, "request_contract_fallback_approval", None)
        fallback = (
            await fallback_request()
            if fallback_request is not None
            else {"approved": False, "reason": "CLIENT_CAPABILITY_UNAVAILABLE"}
        )
        response = await self.client.pull_contracts(self._installed())
        response["fallback_approval"] = fallback
        items = response.get("items", [])
        if not isinstance(items, list):
            raise EdgeContractError("CONTRACT_PULL_SCHEMA_INVALID")
        for item in items:
            if not isinstance(item, dict) or not isinstance(item.get("delivery_id"), str):
                raise EdgeContractError("CONTRACT_PULL_SCHEMA_INVALID")
            state = self._persist(item, item["delivery_id"])
            try:
                await self.client.acknowledge_contract(
                    state.delivery_id,
                    {
                        "status": "ACTIVE",
                        "contract_version_id": state.cloud_contract_version_id,
                    },
                )
                with self.database.session_factory() as session:
                    current = session.get(ContractDeliveryState, state.id)
                    if current:
                        current.acknowledged_at = utcnow()
                        current.error_code = None
                        current.error_message = None
                        session.commit()
            except Exception as exc:
                with self.database.session_factory() as session:
                    current = session.get(ContractDeliveryState, state.id)
                    if current:
                        current.attempt_count += 1
                        current.error_code = type(exc).__name__
                        current.error_message = str(exc)[:500]
                        session.commit()
        return response


class HardwareCommandSyncAgent:
    ACTIONS = {
        "ACTIVATE_DEVICE_RUNTIME",
        "DEACTIVATE_DEVICE_RUNTIME",
        "DECOMMISSION_DEVICE",
        "RESTART_DEVICE_RUNTIME",
        "REFRESH_PORT_INVENTORY",
        "TEST_DEVICE_COMMUNICATION",
        "SET_PUMP_PRICE",
        "AUTHORIZE_FUELING_PRESET",
        "LOCK_FUELING_AUTHORIZATION",
    }

    def __init__(
        self,
        database: Database,
        identity: LocalIdentity,
        client: CloudControlPlaneClient,
        runtime_manager: ProductionTankRuntimeManager | None = None,
        pump_runtime_manager: ProductionPumpRuntimeManager | None = None,
        priceboard_runtime_manager: ProductionPriceBoardRuntimeManager | None = None,
    ) -> None:
        self.database = database
        self.identity = identity
        self.client = client
        self.authorization = ContractAuthorizationService()
        self.runtime_manager = runtime_manager
        self.pump_runtime_manager = pump_runtime_manager
        self.priceboard_runtime_manager = priceboard_runtime_manager
        self.customer_hardware_fueling_enabled = os.getenv(
            "CUSTOMER_HARDWARE_FUELING_ENABLED", "false"
        ).lower() in {"1", "true"}

    @staticmethod
    def _expiry(value: object) -> datetime:
        if not isinstance(value, str):
            raise EdgeContractError("HARDWARE_COMMAND_EXPIRY_INVALID")
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None or parsed <= datetime.now(UTC):
            raise EdgeContractError("HARDWARE_COMMAND_EXPIRED")
        return parsed

    def _verify(self, session: Session, item: dict[str, object]) -> tuple[dict[str, object], str]:
        if item.get("signature_algorithm") != "Ed25519":
            raise EdgeContractError("HARDWARE_COMMAND_SIGNATURE_ALGORITHM_INVALID")
        payload, envelope = item.get("payload"), item.get("envelope")
        if not isinstance(payload, dict) or not isinstance(envelope, dict):
            raise EdgeContractError("HARDWARE_COMMAND_SCHEMA_INVALID")
        digest = hashlib.sha256(canonical_json(payload)).hexdigest()
        if not secrets.compare_digest(digest, str(item.get("payload_hash", ""))):
            raise EdgeContractError("HARDWARE_COMMAND_HASH_MISMATCH")
        if envelope.get("payload") != payload or envelope.get("payload_hash") != digest:
            raise EdgeContractError("HARDWARE_COMMAND_ENVELOPE_MISMATCH")
        if payload.get("edge_device_uuid") != self.identity.device_uuid:
            raise EdgeContractError("HARDWARE_COMMAND_WRONG_EDGE")
        action = str(payload.get("action", ""))
        if action not in self.ACTIONS:
            raise EdgeContractError("REJECTED_UNKNOWN_ACTION")
        self._expiry(payload.get("expires_at"))
        if action in {"AUTHORIZE_FUELING_PRESET", "LOCK_FUELING_AUTHORIZATION"}:
            if not self.customer_hardware_fueling_enabled:
                raise EdgeContractError("CUSTOMER_HARDWARE_FUELING_DISABLED")
            forbidden = {"raw_hex", "frame_hex", "hex", "text_12"}
            if forbidden.intersection(payload):
                raise EdgeContractError("RAW_PROTOCOL_DATA_FORBIDDEN")
            required = {"fueling_session_id", "customer_id", "company_id", "station_id",
                "pump_id", "nozzle_id", "pump_address", "requested_amount", "unit_price",
                "fuel_code", "currency", "protocol_code", "protocol_version", "protocol_hash",
                "expires_at", "idempotency_key", "correlation_id", "session_status"}
            if required - payload.keys():
                raise EdgeContractError("CUSTOMER_FUELING_COMMAND_SCHEMA_INVALID")
            if payload.get("currency") != "SAR":
                raise EdgeContractError("CUSTOMER_FUELING_CURRENCY_INVALID")
            permitted_states = ({"AUTHORIZATION_QUEUED"} if action == "AUTHORIZE_FUELING_PRESET"
                else {"CANCELLED", "EXPIRED", "SETTLED", "AUTHORIZATION_EXPIRED", "RUNTIME_RECOVERY", "STARTUP_FAIL_SAFE"})
            if payload.get("session_status") not in permitted_states:
                raise EdgeContractError("CUSTOMER_FUELING_SESSION_STATE_INVALID")
        key_id = str(item.get("signing_key_id", ""))
        key = session.scalar(
            select(TrustedCloudSigningKey).where(
                TrustedCloudSigningKey.key_id == key_id,
                TrustedCloudSigningKey.status == "ACTIVE",
            )
        )
        if key is None:
            raise EdgeContractError("HARDWARE_COMMAND_SIGNING_KEY_UNTRUSTED")
        try:
            Ed25519PublicKey.from_public_bytes(unb64(key.public_key_encoded)).verify(
                unb64(str(item.get("signature", ""))), canonical_json(envelope)
            )
        except (ValueError, InvalidSignature) as exc:
            raise EdgeContractError("HARDWARE_COMMAND_SIGNATURE_INVALID") from exc
        device_type = str(payload.get("device_type") or "TANK_GAUGE")
        self.authorization.authorize_hardware(
            session,
            device_type=device_type,
            stable_identity=str(payload.get("stable_port_identity", "")),
            protocol_code=str(payload.get("protocol_code", "")),
            command_class=(
                "READ_ONLY" if action == "TEST_DEVICE_COMMUNICATION" else "RUNTIME_CONTROL"
            ),
        )
        if action == "TEST_DEVICE_COMMUNICATION":
            expected_capability = {
                "TANK_GAUGE": "READ_PROBE_MEASUREMENT",
                "FUEL_PUMP": "READ_STATUS",
                "PRICE_BOARD": "TEST_COMMUNICATION",
            }.get(device_type)
            if (
                expected_capability is None
                or payload.get("capability") != expected_capability
                or payload.get("persistent") is not False
                or not payload.get("diagnostic_id")
            ):
                raise EdgeContractError("DIAGNOSTIC_SCHEMA_INVALID")
        else:
            configuration = session.scalar(
                select(StagedDeviceConfiguration).where(
                    StagedDeviceConfiguration.cloud_device_id
                    == str(payload.get("device_uuid", "")),
                    StagedDeviceConfiguration.configuration_version_id
                    == str(payload.get("configuration_version_id", "")),
                    StagedDeviceConfiguration.status == "STAGED",
                )
            )
            if configuration is None:
                raise EdgeContractError("SIGNED_STAGED_CONFIGURATION_REQUIRED")
            if (
                configuration.serial_port_identity != str(payload.get("stable_port_identity", ""))
                or configuration.protocol_code != str(payload.get("protocol_code", ""))
                or configuration.device_type != device_type
            ):
                raise EdgeContractError("HARDWARE_COMMAND_CONFIGURATION_MISMATCH")
            configured_address = str(payload.get("board_address") if device_type == "PRICE_BOARD"
                else payload.get("pump_address") if action in {"AUTHORIZE_FUELING_PRESET", "LOCK_FUELING_AUTHORIZATION"}
                else payload.get("probe_serial", ""))
            if (
                action not in {"SET_PUMP_PRICE", "AUTHORIZE_FUELING_PRESET", "LOCK_FUELING_AUTHORIZATION"}
                and configuration.device_address != configured_address
            ):
                raise EdgeContractError("HARDWARE_COMMAND_CONFIGURATION_MISMATCH")
            if action in {"AUTHORIZE_FUELING_PRESET", "LOCK_FUELING_AUTHORIZATION"}:
                if device_type != "FUEL_PUMP":
                    raise EdgeContractError("CUSTOMER_FUELING_REQUIRES_FUEL_PUMP")
                target = _address(payload.get("pump_address"))
                matching = [item for item in (configuration.protocol_config_json or {}).get("nozzles", [])
                    if _address(item.get("address")) == target]
                if len(matching) != 1 or str(matching[0].get("id")) != str(payload.get("nozzle_id")):
                    raise EdgeContractError("EXACT_NOZZLE_MAPPING_REQUIRED")
                if str(matching[0].get("fuel_code")) != str(payload.get("fuel_code")):
                    raise EdgeContractError("EXACT_FUEL_TYPE_MISMATCH")
                try:
                    amount = Decimal(str(payload.get("requested_amount")))
                    price = Decimal(str(payload.get("unit_price")))
                except (InvalidOperation, ValueError) as exc:
                    raise EdgeContractError("CUSTOMER_FUELING_AMOUNT_INVALID") from exc
                if amount < Decimal("1.00") or amount > Decimal("9999.99") or price < Decimal("0.01") or price > Decimal("99.99"):
                    raise EdgeContractError("CUSTOMER_FUELING_AMOUNT_OUT_OF_RANGE")
            if action == "SET_PUMP_PRICE":
                if device_type != "FUEL_PUMP" or payload.get("capability") != "SET_PRICE":
                    raise EdgeContractError("PUMP_PRICE_COMMAND_SCHEMA_INVALID")
                target = _address(payload.get("target_nozzle_address"))
                allowed = {
                    _address(item.get("address"))
                    for item in (configuration.protocol_config_json or {}).get("nozzles", [])
                }
                if target not in allowed:
                    raise EdgeContractError("PUMP_PRICE_TARGET_NOT_CONFIGURED")
                try:
                    price = Decimal(str(payload.get("new_unit_price")))
                except (InvalidOperation, ValueError) as exc:
                    raise EdgeContractError("PUMP_PRICE_INVALID") from exc
                if price < Decimal("0.01") or price > Decimal("99.99"):
                    raise EdgeContractError("PUMP_PRICE_OUT_OF_RANGE")
        protocol = session.scalar(
            select(EdgeProtocolVersion).where(
                EdgeProtocolVersion.protocol_code == str(payload.get("protocol_code", "")),
                EdgeProtocolVersion.protocol_version == str(payload.get("protocol_version", "")),
                EdgeProtocolVersion.definition_hash == str(payload.get("protocol_hash", "")),
                EdgeProtocolVersion.status == "VERIFIED",
            )
        )
        if protocol is None:
            raise EdgeContractError("VERIFIED_PROTOCOL_REQUIRED")
        port = session.scalar(
            select(SerialPort).where(
                SerialPort.stable_identity == str(payload.get("stable_port_identity", ""))
            )
        )
        bridge_reuse = bool(
            device_type == "FUEL_PUMP"
            and self.pump_runtime_manager
            and self.pump_runtime_manager.can_reuse(
                str(payload.get("stable_port_identity", "")),
                port.owner_service if port else None,
            )
        )
        if port is None or (port.status != "AVAILABLE" and not bridge_reuse):
            raise EdgeContractError("PORT_NOT_AVAILABLE")
        if (port.owner_process or port.owner_service or port.owner_pid) and not bridge_reuse:
            raise EdgeContractError("PORT_BUSY_EXTERNAL")
        return payload, action

    async def _execute_authorized(
        self,
        delivery_id: str,
        payload: dict[str, object],
        action: str,
    ) -> None:
        device_type = str(payload.get("device_type") or "TANK_GAUGE")
        manager = {
            "FUEL_PUMP": self.pump_runtime_manager,
            "PRICE_BOARD": self.priceboard_runtime_manager,
        }.get(device_type, self.runtime_manager)
        if manager is None or not manager.enabled:
            return
        with self.database.session_factory() as session:
            row = session.scalar(
                select(HardwareCommandInbox).where(HardwareCommandInbox.delivery_id == delivery_id)
            )
            if row is None or row.status not in {"AUTHORIZED", "EXECUTING"}:
                return
            row.status = "EXECUTING"
            session.commit()
        await self.client.acknowledge_hardware_command(delivery_id, {"status": "EXECUTING"})
        if action == "ACTIVATE_DEVICE_RUNTIME":
            result = await manager.activate(payload)
        elif action == "TEST_DEVICE_COMMUNICATION":
            result = await manager.test_communication(payload)
        elif action == "SET_PUMP_PRICE":
            result = await manager.set_price(payload)
        elif action == "AUTHORIZE_FUELING_PRESET":
            result = await manager.authorize_fueling_preset(payload)
        elif action == "LOCK_FUELING_AUTHORIZATION":
            result = await manager.lock_fueling_authorization(payload)
        else:
            result = await manager.deactivate(payload)
        with self.database.session_factory() as session:
            row = session.scalar(
                select(HardwareCommandInbox).where(HardwareCommandInbox.delivery_id == delivery_id)
            )
            if row:
                row.status = "SUCCEEDED"
                row.executed_at = utcnow()
                row.failure_code = None
                row.failure_message = None
                session.commit()
        await self.client.acknowledge_hardware_command(
            delivery_id,
            {"status": "SUCCEEDED", "result": result},
        )

    async def resume_authorized(self) -> None:
        """Resume only commands proven not to have crossed the TX boundary."""
        unknown_results: list[str] = []
        with self.database.session_factory() as session:
            executing = list(
                session.scalars(
                    select(HardwareCommandInbox).where(
                        HardwareCommandInbox.status == "EXECUTING"
                    )
                ).all()
            )
            for row in executing:
                # A restart after EXECUTING may have happened before or after
                # serial ACK. Replaying would risk a second SELECT+command.
                row.status = "FAILED"
                row.failure_code = "EXECUTION_RESULT_UNKNOWN_NO_REPLAY"
                row.failure_message = (
                    "Command crossed the execution boundary; automatic replay is forbidden"
                )
                unknown_results.append(row.delivery_id)
            session.commit()
        for delivery_id in unknown_results:
            await self.client.acknowledge_hardware_command(
                delivery_id,
                {
                    "status": "FAILED",
                    "error_code": "EXECUTION_RESULT_UNKNOWN_NO_REPLAY",
                },
            )
        if not any(
            manager is not None and manager.enabled
            for manager in (
                self.runtime_manager,
                self.pump_runtime_manager,
                self.priceboard_runtime_manager,
            )
        ):
            return
        with self.database.session_factory() as session:
            rows = list(
                session.scalars(
                    select(HardwareCommandInbox).where(
                        HardwareCommandInbox.status == "AUTHORIZED"
                    )
                ).all()
            )
            pending = [
                (
                    row.delivery_id,
                    dict(row.signed_envelope_json.get("payload") or {}),
                    row.action,
                )
                for row in rows
            ]
        for delivery_id, payload, action in pending:
            try:
                await self._execute_authorized(delivery_id, payload, action)
            except Exception as exc:
                with self.database.session_factory() as session:
                    row = session.scalar(
                        select(HardwareCommandInbox).where(
                            HardwareCommandInbox.delivery_id == delivery_id
                        )
                    )
                    if row:
                        row.status = "FAILED"
                        row.failure_code = str(exc)[:100]
                        row.failure_message = str(exc)[:500]
                        session.commit()
                await self.client.acknowledge_hardware_command(
                    delivery_id, {"status": "FAILED", "error_code": str(exc)[:100]}
                )

    async def recover_persistent(self) -> dict[str, int]:
        totals = {"recovered": 0, "failed": 0}
        for manager in (
            self.runtime_manager,
            self.pump_runtime_manager,
            self.priceboard_runtime_manager,
        ):
            if manager is None:
                continue
            result = await manager.recover_persistent()
            totals["recovered"] += result.get("recovered", 0)
            totals["failed"] += result.get("failed", 0)
        return totals

    async def sync_once(self) -> dict[str, object]:
        await self.resume_authorized()
        response = await self.client.pull_hardware_commands({})
        items = response.get("items", [])
        if not isinstance(items, list):
            raise EdgeContractError("HARDWARE_COMMAND_PULL_SCHEMA_INVALID")
        for item in items:
            if not isinstance(item, dict) or not isinstance(item.get("delivery_id"), str):
                raise EdgeContractError("HARDWARE_COMMAND_PULL_SCHEMA_INVALID")
            delivery_id = item["delivery_id"]
            with self.database.session_factory() as session:
                row = session.scalar(
                    select(HardwareCommandInbox).where(
                        HardwareCommandInbox.delivery_id == delivery_id
                    )
                )
                if row is not None and row.status != "RECEIVED":
                    # Cloud intentionally redelivers DELIVERED items until it
                    # receives an ACK. Re-ACK the durable local outcome but
                    # never verify or execute the same delivery twice.
                    ack = {"status": row.status}
                    if row.failure_code:
                        ack["error_code"] = row.failure_code
                    await self.client.acknowledge_hardware_command(delivery_id, ack)
                    continue
                if row is None:
                    payload = item.get("payload")
                    if not isinstance(payload, dict):
                        raise EdgeContractError("HARDWARE_COMMAND_SCHEMA_INVALID")
                    row = HardwareCommandInbox(
                        delivery_id=delivery_id,
                        command_id=str(payload.get("request_id", delivery_id)),
                        action=str(payload.get("action", "")),
                        cloud_device_id=str(
                            payload.get("device_uuid")
                            or f"diagnostic:{payload.get('diagnostic_id', delivery_id)}"
                        ),
                        contract_version_id=int(payload.get("contract_version_id", 0)),
                        configuration_version_id=str(payload.get("configuration_version_id", "0")),
                        payload_hash=str(item.get("payload_hash", "")),
                        signed_envelope_json=dict(item.get("envelope") or {}),
                        signature=str(item.get("signature", "")),
                        signing_key_id=str(item.get("signing_key_id", "")),
                        status="RECEIVED",
                    )
                    session.add(row)
                    session.commit()
                    if row.action == "TEST_DEVICE_COMMUNICATION":
                        await self.client.acknowledge_hardware_command(
                            delivery_id, {"status": "RECEIVED"}
                        )
                try:
                    payload, action = self._verify(session, item)
                    row.action = action
                    row.status = "AUTHORIZED"
                    row.verified_at = utcnow()
                    row.authorized_at = utcnow()
                    session.commit()
                    await self.client.acknowledge_hardware_command(
                        delivery_id, {"status": "AUTHORIZED"}
                    )
                    await self._execute_authorized(delivery_id, payload, action)
                except Exception as exc:
                    with self.database.session_factory() as failure_session:
                        failed = failure_session.scalar(
                            select(HardwareCommandInbox).where(
                                HardwareCommandInbox.delivery_id == delivery_id
                            )
                        )
                        if failed:
                            failed.status = (
                                "FAILED" if failed.verified_at is not None else "REJECTED"
                            )
                            failed.failure_code = str(exc)[:100]
                            failed.failure_message = str(exc)[:500]
                            failure_session.commit()
                            failed_status = failed.status
                        else:
                            failed_status = "REJECTED"
                    await self.client.acknowledge_hardware_command(
                        delivery_id,
                        {"status": failed_status, "error_code": str(exc)[:100]},
                    )
        return response
