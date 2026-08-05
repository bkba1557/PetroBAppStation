import hashlib
import hmac
import json
import time
from datetime import datetime, timezone

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    Company, Customer, CustomerPaymentIntent, CustomerQrToken, CustomerWallet,
    FuelingSession, Nozzle, PaymentWebhookEvent, Pump, PumpCommand, ShiftSession,
    Station, Vehicle, WalletHold, WalletTransaction,
)


EMAIL = "customer-api-test@nnexoris.invalid"
PASSWORD = "Test-Only-Password-2026"
QR_RAW = "NNEXORIS-TEST-QR-TOKEN-0001"


@pytest.fixture(autouse=True)
def customer_foundation(app):
    engine = app.extensions["unified_engine"]
    app.config.update(
        CUSTOMER_DEFAULT_COMPANY_KEY="broq",
        CUSTOMER_JWT_SECRET="customer-test-jwt-secret-32-bytes-minimum",
        CUSTOMER_HARDWARE_FUELING_ENABLED=False,
        STRIPE_MODE="test",
        STRIPE_SECRET_KEY="sk_test_unit_only",
        STRIPE_PUBLISHABLE_KEY="pk_test_unit_only",
        STRIPE_WEBHOOK_SECRET="whsec_unit_only",
    )
    with Session(engine) as db:
        company = Company(company_key="broq", name_ar="بروق", name_en="Broq",
                          lifecycle_status="ACTIVE", enabled=True,
                          customer_self_service_enabled=True)
        db.add(company); db.flush()
        station = db.scalar(select(Station).where(Station.station_id == "STATION-HAIL-001"))
        station.company_id = company.id
        station.customer_self_service_enabled = True
        station.self_service_status = "PILOT"
        station.require_operator_confirmation = True
        station.minimum_customer_amount = 5
        station.maximum_customer_amount = 100
        pump = db.scalar(select(Pump).where(Pump.station_id == station.id))
        nozzle = db.scalar(select(Nozzle).where(Nozzle.pump_id == pump.id))
        pump.enabled = True; pump.status = "ready"
        nozzle.enabled = True; nozzle.status = "ready"
        db.add(ShiftSession(company_id=company.id, station_id=station.id,
            shift_slot="test", shift_label="Customer API Test", mode="single",
            planned_start_time="00:00", planned_end_time="23:59",
            actual_started_at=datetime.now(timezone.utc), status="active",
            summary_json={}, metadata_json={}))
        db.add(CustomerQrToken(token_hash=hashlib.sha256(QR_RAW.encode()).hexdigest(),
            station_id=station.id, pump_id=pump.id, nozzle_id=nozzle.id, enabled=True))
        db.commit()


def register(client):
    response = client.post("/api/v1/customer/auth/register", json={
        "email": EMAIL, "password": PASSWORD, "displayName": "Customer API Test",
        "vehicle": {"plateNumber": "TEST-2026", "registrationNumber": "REG-TEST-2026"},
    }, headers={"X-Device-Id": "test-device", "X-Correlation-Id": "test-correlation"})
    assert response.status_code == 201, response.get_data(as_text=True)
    return response.get_json()


def authorization(payload):
    return {"Authorization": f"Bearer {payload['tokens']['accessToken']}",
            "X-Device-Id": "test-device"}


def stripe_signature(raw):
    timestamp = int(time.time())
    value = hmac.new(b"whsec_unit_only", str(timestamp).encode() + b"." + raw,
                     hashlib.sha256).hexdigest()
    return f"t={timestamp},v1={value}"


def successful_topup(client, app, monkeypatch, auth, amount="25.00"):
    monkeypatch.setattr("app.customer_api.wallet.create_stripe_payment_intent",
        lambda **_: {"id": "pi_customer_test_001", "client_secret": "pi_customer_test_001_secret_test"})
    created = client.post("/api/v1/customer/wallet/topups", json={"amount": amount},
        headers={**auth, "Idempotency-Key": "topup-test-001"})
    assert created.status_code == 201, created.get_data(as_text=True)
    event = {"id": "evt_customer_test_001", "type": "payment_intent.succeeded",
        "data": {"object": {"id": "pi_customer_test_001", "amount_received": 2500, "currency": "sar"}}}
    raw = json.dumps(event, separators=(",", ":")).encode()
    webhook = client.post("/api/v1/customer/payments/stripe/webhook", data=raw,
        headers={"Stripe-Signature": stripe_signature(raw), "Content-Type": "application/json"})
    assert webhook.status_code == 200, webhook.get_data(as_text=True)
    return created.get_json(), event


def test_health_auth_profile_station_and_vehicle_flow(client, app):
    health = client.get("/api/v1/customer/health")
    assert health.status_code == 200
    assert health.get_json()["hardwareFuelingEnabled"] is False
    payload = register(client); auth = authorization(payload)
    assert payload["customer"]["role"] == "CUSTOMER"
    assert payload["tokens"]["accessTokenExpiresAt"]
    login = client.post("/api/v1/customer/auth/login", json={"email": EMAIL, "password": PASSWORD},
                        headers={"X-Device-Id": "test-device"})
    assert login.status_code == 200
    assert client.get("/api/v1/customer/profile", headers=auth).get_json()["email"] == EMAIL
    stations = client.get("/api/v1/customer/stations", headers=auth)
    assert stations.status_code == 200 and len(stations.get_json()) == 1
    assert stations.get_json()[0]["appFuelingAvailable"] is False
    station_id = stations.get_json()[0]["id"]
    assert client.get(f"/api/v1/customer/stations/{station_id}/prices", headers=auth).status_code == 200
    vehicles = client.get("/api/v1/customer/vehicles", headers=auth).get_json()
    assert vehicles[0]["registrationNumber"] == "REG-TEST-2026"
    added = client.post("/api/v1/customer/vehicles", json={"plateNumber": "TEST-2027",
        "registrationNumber": "REG-2", "fuelCode": "gasoline91"}, headers=auth)
    assert added.status_code == 201
    vehicle_id = added.get_json()["id"]
    assert client.patch(f"/api/v1/customer/vehicles/{vehicle_id}", json={"nickname": "My Car"}, headers=auth).status_code == 200
    assert client.delete(f"/api/v1/customer/vehicles/{vehicle_id}", headers=auth).status_code == 204


def test_refresh_rotation_and_reuse_revokes_family(client):
    payload = register(client)
    first = payload["tokens"]["refreshToken"]
    rotated = client.post("/api/v1/customer/auth/refresh", json={"refreshToken": first})
    assert rotated.status_code == 200
    reuse = client.post("/api/v1/customer/auth/refresh", json={"refreshToken": first})
    assert reuse.status_code == 401
    assert reuse.get_json()["error"] == "REFRESH_TOKEN_REUSE_DETECTED"
    replacement = client.post("/api/v1/customer/auth/refresh",
                              json={"refreshToken": rotated.get_json()["refreshToken"]})
    assert replacement.status_code == 401


def test_stripe_webhook_is_only_credit_source_and_is_idempotent(client, app, monkeypatch):
    payload = register(client); auth = authorization(payload)
    monkeypatch.setattr("app.customer_api.wallet.create_stripe_payment_intent",
        lambda **_: {"id": "pi_customer_test_001", "client_secret": "secret"})
    created = client.post("/api/v1/customer/wallet/topups", json={"amount": "25.00"},
        headers={**auth, "Idempotency-Key": "topup-test-001"})
    assert created.status_code == 201
    assert client.get("/api/v1/customer/wallet", headers=auth).get_json()["balance"]["available"] == 0
    event = {"id": "evt_customer_test_001", "type": "payment_intent.succeeded",
        "data": {"object": {"id": "pi_customer_test_001", "amount_received": 2500, "currency": "sar"}}}
    raw = json.dumps(event, separators=(",", ":")).encode(); signature = stripe_signature(raw)
    first = client.post("/api/v1/customer/payments/stripe/webhook", data=raw,
        headers={"Stripe-Signature": signature, "Content-Type": "application/json"})
    second = client.post("/api/v1/customer/payments/stripe/webhook", data=raw,
        headers={"Stripe-Signature": signature, "Content-Type": "application/json"})
    assert first.status_code == second.status_code == 200
    assert second.get_json()["duplicate"] is True
    wallet = client.get("/api/v1/customer/wallet", headers=auth).get_json()
    assert wallet["balance"]["available"] == 25.0 and wallet["balance"]["version"] == 1
    with Session(app.extensions["unified_engine"]) as db:
        entries = db.scalars(select(WalletTransaction)).all()
        assert len(entries) == 1 and entries[0].transaction_type == "TOPUP_CREDIT"
        assert len(db.scalars(select(PaymentWebhookEvent)).all()) == 1


def test_fueling_foundation_holds_funds_but_never_creates_hardware_command(client, app, monkeypatch):
    payload = register(client); auth = authorization(payload)
    successful_topup(client, app, monkeypatch, auth)
    resolved = client.post("/api/v1/customer/qr/resolve", json={"token": QR_RAW}, headers=auth)
    assert resolved.status_code == 200 and resolved.get_json()["valid"] is True
    session = client.post("/api/v1/customer/fueling-sessions", json={
        "qrResolutionId": resolved.get_json()["resolution"]["resolutionId"],
        "requestedMode": "fixedAmount", "requestedAmount": 10.0,
    }, headers={**auth, "Idempotency-Key": "fueling-test-001"})
    assert session.status_code == 201, session.get_data(as_text=True)
    assert session.get_json()["status"] == "FUNDS_HELD"
    assert session.get_json()["hardwareActivationEnabled"] is False
    wallet = client.get("/api/v1/customer/wallet", headers=auth).get_json()["balance"]
    assert wallet["available"] == 15.0 and wallet["reserved"] == 10.0
    events = client.get("/api/v1/customer/realtime?once=1", headers=auth)
    assert events.status_code == 200 and b"FUELING_SESSION_UPDATED" in events.data
    with Session(app.extensions["unified_engine"]) as db:
        assert len(db.scalars(select(FuelingSession)).all()) == 1
        assert len(db.scalars(select(WalletHold)).all()) == 1
        assert db.scalars(select(PumpCommand)).all() == []
    cancelled = client.post(f"/api/v1/customer/fueling-sessions/{session.get_json()['sessionId']}/cancel",
        headers={**auth, "Idempotency-Key": "cancel-test-001"})
    assert cancelled.status_code == 200 and cancelled.get_json()["status"] == "CANCELLED"
    wallet = client.get("/api/v1/customer/wallet", headers=auth).get_json()["balance"]
    assert wallet["available"] == 25.0 and wallet["reserved"] == 0.0


def test_invalid_stripe_signature_cannot_credit_wallet(client, app, monkeypatch):
    payload = register(client); auth = authorization(payload)
    monkeypatch.setattr("app.customer_api.wallet.create_stripe_payment_intent",
        lambda **_: {"id": "pi_customer_test_001", "client_secret": "secret"})
    client.post("/api/v1/customer/wallet/topups", json={"amount": "25.00"},
        headers={**auth, "Idempotency-Key": "topup-test-001"})
    raw = b'{"id":"evt_bad","type":"payment_intent.succeeded","data":{"object":{"id":"pi_customer_test_001","amount_received":2500,"currency":"sar"}}}'
    response = client.post("/api/v1/customer/payments/stripe/webhook", data=raw,
        headers={"Stripe-Signature": f"t={int(time.time())},v1=bad"})
    assert response.status_code == 400
    assert client.get("/api/v1/customer/wallet", headers=auth).get_json()["balance"]["available"] == 0


def test_company_self_service_disabled_keeps_station_visible_and_blocks_qr(client, app):
    payload = register(client); auth = authorization(payload)
    with Session(app.extensions["unified_engine"]) as db:
        company = db.scalar(select(Company).where(Company.company_key == "broq"))
        company.customer_self_service_enabled = False
        db.commit()
    stations = client.get("/api/v1/customer/stations", headers=auth).get_json()
    assert len(stations) == 1
    assert stations[0]["stationVisible"] is True
    assert stations[0]["selfServiceEnabled"] is False
    assert stations[0]["availabilityReason"] == "COMPANY_SELF_SERVICE_DISABLED"
    denied = client.post("/api/v1/customer/qr/resolve", json={"token": QR_RAW}, headers=auth)
    assert denied.status_code == 200
    assert denied.get_json() == {"valid": False, "code": "DISPENSER_UNAVAILABLE"}


def test_station_self_service_disabled_keeps_station_visible_and_blocks_qr(client, app):
    payload = register(client); auth = authorization(payload)
    with Session(app.extensions["unified_engine"]) as db:
        station = db.scalar(select(Station).where(Station.station_id == "STATION-HAIL-001"))
        station.customer_self_service_enabled = False
        db.commit()
    stations = client.get("/api/v1/customer/stations", headers=auth).get_json()
    assert len(stations) == 1
    assert stations[0]["stationVisible"] is True
    assert stations[0]["selfServiceEnabled"] is False
    assert stations[0]["availabilityReason"] == "STATION_SELF_SERVICE_DISABLED"
    denied = client.post("/api/v1/customer/qr/resolve", json={"token": QR_RAW}, headers=auth)
    assert denied.status_code == 200
    assert denied.get_json()["code"] == "DISPENSER_UNAVAILABLE"


def test_full_tank_is_disabled_and_aggregated_apis_are_customer_scoped(client, app, monkeypatch):
    payload = register(client); auth = authorization(payload)
    successful_topup(client, app, monkeypatch, auth)
    dashboard = client.get("/api/v1/customer/dashboard", headers=auth)
    analytics = client.get("/api/v1/customer/analytics?period=30d", headers=auth)
    transactions = client.get("/api/v1/customer/transactions", headers=auth)
    assert dashboard.status_code == analytics.status_code == transactions.status_code == 200
    assert dashboard.get_json()["wallet"]["available"] == 25.0
    assert len(transactions.get_json()["items"]) == 1
    transaction_id = transactions.get_json()["items"][0]["id"]
    assert client.get(f"/api/v1/customer/transactions/{transaction_id}", headers=auth).status_code == 200
    assert client.patch(f"/api/v1/customer/transactions/{transaction_id}", headers=auth).status_code == 405
    resolved = client.post("/api/v1/customer/qr/resolve", json={"token": QR_RAW}, headers=auth).get_json()
    denied = client.post("/api/v1/customer/fueling-sessions", json={
        "qrResolutionId": resolved["resolution"]["resolutionId"],
        "requestedMode": "fullTank", "requestedAmount": 10,
    }, headers={**auth, "Idempotency-Key": "full-tank-disabled"})
    assert denied.status_code == 409
    assert denied.get_json()["error"] == "CUSTOMER_FULL_TANK_DISABLED"


def test_company_is_derived_from_station_for_cross_company_customer(client, app, monkeypatch):
    payload = register(client); auth = authorization(payload)
    successful_topup(client, app, monkeypatch, auth)
    with Session(app.extensions["unified_engine"]) as db:
        station = db.scalar(select(Station).where(Station.station_id == "STATION-HAIL-001"))
        other = Company(company_key="other", name_ar="شركة أخرى", name_en="Other",
            lifecycle_status="ACTIVE", enabled=True, customer_self_service_enabled=True)
        db.add(other); db.flush()
        station.company_id = other.id
        db.commit(); other_id = other.id
    resolved = client.post("/api/v1/customer/qr/resolve", json={"token": QR_RAW}, headers=auth)
    assert resolved.status_code == 200 and resolved.get_json()["valid"] is True
    created = client.post("/api/v1/customer/fueling-sessions", json={
        "qrResolutionId": resolved.get_json()["resolution"]["resolutionId"],
        "requestedMode": "fixedAmount", "requestedAmount": 10,
    }, headers={**auth, "Idempotency-Key": "cross-company-station-derived"})
    assert created.status_code == 201, created.get_data(as_text=True)
    with Session(app.extensions["unified_engine"]) as db:
        fueling = db.scalar(select(FuelingSession).where(
            FuelingSession.public_id == created.get_json()["sessionId"]))
        assert fueling.company_id == other_id
        hold_entry = db.scalar(select(WalletTransaction).where(
            WalletTransaction.transaction_type == "FUELING_HOLD"))
        assert hold_entry.company_id == other_id


def test_vehicle_fuel_mismatch_requires_explicit_confirmation(client, app, monkeypatch):
    payload = register(client); auth = authorization(payload)
    successful_topup(client, app, monkeypatch, auth)
    vehicle = client.post("/api/v1/customer/vehicles", json={"plateNumber": "DIESEL-1",
        "registrationNumber": "DIESEL-REG", "fuelCode": "diesel"}, headers=auth).get_json()
    resolved = client.post("/api/v1/customer/qr/resolve", json={"token": QR_RAW}, headers=auth).get_json()
    denied = client.post("/api/v1/customer/fueling-sessions", json={
        "qrResolutionId": resolved["resolution"]["resolutionId"], "vehicleId": vehicle["id"],
        "requestedMode": "fixedAmount", "requestedAmount": 10,
    }, headers={**auth, "Idempotency-Key": "wrong-fuel-type"})
    assert denied.status_code == 409
    assert denied.get_json()["error"] == "VEHICLE_FUEL_MISMATCH_CONFIRMATION_REQUIRED"


def test_stripe_amount_mismatch_is_rejected_without_ledger_credit(client, app, monkeypatch):
    payload = register(client); auth = authorization(payload)
    monkeypatch.setattr("app.customer_api.wallet.create_stripe_payment_intent",
        lambda **_: {"id": "pi_amount_mismatch", "client_secret": "secret"})
    created = client.post("/api/v1/customer/wallet/topups", json={"amount": "25.00"},
        headers={**auth, "Idempotency-Key": "amount-mismatch"})
    assert created.status_code == 201
    event = {"id": "evt_amount_mismatch", "type": "payment_intent.succeeded",
        "data": {"object": {"id": "pi_amount_mismatch", "amount_received": 2400, "currency": "sar"}}}
    raw = json.dumps(event, separators=(",", ":")).encode()
    response = client.post("/api/v1/customer/payments/stripe/webhook", data=raw,
        headers={"Stripe-Signature": stripe_signature(raw), "Content-Type": "application/json"})
    assert response.status_code == 409
    with Session(app.extensions["unified_engine"]) as db:
        assert db.scalars(select(WalletTransaction)).all() == []


def test_customer_audit_actions_are_canonical_and_safe(client, app):
    payload = register(client); auth = authorization(payload)
    client.post("/api/v1/customer/auth/login", json={"email": EMAIL, "password": PASSWORD},
        headers={"X-Device-Id": "audit-device"})
    client.post("/api/v1/customer/auth/logout", headers=auth)
    with Session(app.extensions["unified_engine"]) as db:
        from app.models import CustomerAuditEvent
        actions = set(db.scalars(select(CustomerAuditEvent.action)).all())
        assert {"CUSTOMER_REGISTERED", "CUSTOMER_LOGGED_IN", "CUSTOMER_LOGGED_OUT"} <= actions
        details = db.scalars(select(CustomerAuditEvent.details_json)).all()
        assert all("password" not in json.dumps(item).lower() for item in details)


def test_super_admin_customer_management_and_controlled_hardware_screen(client):
    payload = register(client)
    customer_id = payload["customer"]["id"]
    with client.session_transaction() as state:
        state["unified_role"] = "Super Admin"
        state["unified_username"] = "customer-test-admin"
    listing = client.get("/app-customers")
    detail = client.get(f"/app-customers/{customer_id}")
    controlled = client.get("/customer-hardware-test")
    assert listing.status_code == detail.status_code == controlled.status_code == 200
    assert "عملاء التطبيق" in listing.get_data(as_text=True)
    assert "ACTIVE_FUELING_STOP_NOT_PROVEN" in controlled.get_data(as_text=True)
    assert "TX DISABLED" in controlled.get_data(as_text=True)
    assert client.patch("/api/admin/wallet-ledger/1").status_code == 405
    assert client.delete("/api/admin/wallet-ledger/1").status_code == 405
    assert client.patch("/api/admin/completed-sales/1").status_code == 405
    assert client.delete("/api/admin/completed-sales/1").status_code == 405


def test_super_admin_can_credit_customer_wallet_once_and_customer_can_use_balance(client, app):
    payload = register(client); customer_id = payload["customer"]["id"]
    with client.session_transaction() as state:
        state["unified_role"] = "Super Admin"
        state["unified_username"] = "wallet-credit-admin"
    key = "9dedecb4-1e59-4ff7-8c34-59cbe87df889"
    form = {"amount": "150.00", "reason": "رصيد تعبئة معتمد", "note": "اختبار",
        "idempotency_key": key}
    first = client.post(f"/app-customers/{customer_id}/wallet-credit", data=form)
    second = client.post(f"/app-customers/{customer_id}/wallet-credit", data=form)
    assert first.status_code == second.status_code == 302
    with Session(app.extensions["unified_engine"]) as db:
        customer = db.scalar(select(Customer).where(Customer.public_id == customer_id))
        wallet = db.scalar(select(CustomerWallet).where(CustomerWallet.customer_id == customer.id))
        credits = db.scalars(select(WalletTransaction).where(
            WalletTransaction.wallet_id == wallet.id,
            WalletTransaction.idempotency_key == f"admin-wallet-credit:{key}")).all()
        assert float(wallet.balance) == 150.0
        assert len(credits) == 1 and credits[0].transaction_type == "MANUAL_ADJUSTMENT"
        assert credits[0].metadata_json["operation"] == "ADMIN_WALLET_CREDIT"
        from app.models import CustomerAuditEvent, CustomerRealtimeEvent
        assert db.scalar(select(CustomerAuditEvent.id).where(
            CustomerAuditEvent.customer_id == customer.id,
            CustomerAuditEvent.action == "WALLET_ADMIN_CREDIT_CREATED"))
        assert db.scalar(select(CustomerRealtimeEvent.id).where(
            CustomerRealtimeEvent.customer_id == customer.id,
            CustomerRealtimeEvent.event_type == "WALLET_UPDATED"))
    auth = authorization(payload)
    assert client.get("/api/v1/customer/wallet", headers=auth).get_json()["balance"]["available"] == 150.0


def test_company_admin_cannot_open_controlled_hardware_screen(client, app):
    register(client)
    with Session(app.extensions["unified_engine"]) as db:
        company_id = db.scalar(select(Company.id).where(Company.company_key == "broq"))
    with client.session_transaction() as state:
        state["unified_role"] = "Company Admin"
        state["company_id"] = company_id
    assert client.get("/customer-hardware-test").status_code == 403


def test_self_service_control_forces_pilot_and_valid_schedule(client, app):
    register(client)
    with Session(app.extensions["unified_engine"]) as db:
        company_id = db.scalar(select(Company.id).where(Company.company_key == "broq"))
        station_id = db.scalar(select(Station.id).where(Station.station_id == "STATION-HAIL-001"))
    with client.session_transaction() as state:
        state["unified_role"] = "Super Admin"
    url = f"/api/v1/companies/{company_id}/self-service/stations/{station_id}"
    autonomous = client.patch(url, json={"enabled": True, "status": "ENABLED"})
    assert autonomous.status_code == 409
    missing_schedule = client.patch(url, json={"enabled": True, "status": "SCHEDULED"})
    assert missing_schedule.status_code == 400
    pilot = client.patch(url, json={"enabled": True, "status": "PILOT",
        "minimumAmount": 5, "maximumAmount": 50, "allowedFuelTypes": ["gasoline95"],
        "allowWalletPayment": True, "allowStripeDirectPayment": False})
    assert pilot.status_code == 200
    assert pilot.get_json()["mode"] == "PILOT_OPERATOR_SUPERVISED"
    assert pilot.get_json()["hardwareCommandCreated"] is False
    assert pilot.get_json()["fuelingAmountSource"] == "CUSTOMER_APP_START"
    with Session(app.extensions["unified_engine"]) as db:
        assert db.scalars(select(PumpCommand)).all() == []


def test_enabling_station_automatically_creates_cloud_qr_for_each_nozzle(client, app):
    register(client)
    with Session(app.extensions["unified_engine"]) as db:
        company_id = db.scalar(select(Company.id).where(Company.company_key == "broq"))
        station = db.scalar(select(Station).where(Station.station_id == "STATION-HAIL-001"))
        station.customer_self_service_enabled = False
        for token in db.scalars(select(CustomerQrToken).where(CustomerQrToken.station_id == station.id)):
            token.enabled = False
        station_id = station.id
        enabled_nozzle_count = len(db.scalars(select(Nozzle).where(
            Nozzle.station_id == station.id, Nozzle.enabled.is_(True))).all())
        db.commit()
    with client.session_transaction() as state:
        state["unified_role"] = "Super Admin"
        state["unified_username"] = "qr-auto-test-admin"
    response = client.patch(
        f"/api/v1/companies/{company_id}/self-service/stations/{station_id}",
        json={"enabled": True, "status": "PILOT", "allowWalletPayment": True},
    )
    assert response.status_code == 200
    assert response.get_json()["createdQrCount"] == enabled_nozzle_count
    with Session(app.extensions["unified_engine"]) as db:
        active = db.scalars(select(CustomerQrToken).where(
            CustomerQrToken.station_id == station_id,
            CustomerQrToken.enabled.is_(True),
        )).all()
        assert len(active) == enabled_nozzle_count
        assert all(token.public_id and token.token_ciphertext for token in active)


def test_cloud_generates_printable_real_qr_per_nozzle_and_can_revoke_it(client, app):
    payload = register(client); auth = authorization(payload)
    with Session(app.extensions["unified_engine"]) as db:
        nozzle_id = db.scalar(select(Nozzle.id).where(Nozzle.nozzle_id == "NOZZLE-001"))
        station_id = db.scalar(select(Station.id).where(Station.station_id == "STATION-HAIL-001"))
    with client.session_transaction() as state:
        state["unified_role"] = "Super Admin"
        state["unified_username"] = "qr-test-admin"
    page = client.get(f"/self-service/customer-management?station={station_id}")
    assert page.status_code == 200
    assert "إدارة الخدمات الذاتية" in page.get_data(as_text=True)
    created = client.post(f"/self-service/customer-management/nozzles/{nozzle_id}/qr")
    assert created.status_code == 302
    with Session(app.extensions["unified_engine"]) as db:
        token = db.scalar(select(CustomerQrToken).where(
            CustomerQrToken.nozzle_id == nozzle_id, CustomerQrToken.enabled.is_(True)))
        assert token is not None and token.token_ciphertext and token.public_id
        token_id = token.id
        ciphertext = token.token_ciphertext
    printed = client.get(f"/self-service/customer-management/qr/{token_id}/print")
    assert printed.status_code == 200
    html = printed.get_data(as_text=True)
    assert "data:image/png;base64," in html and "لي" in html
    assert "/static/icons/nxs/logo.PNG" in html
    assert "customer-app-logo.png" not in html
    assert "NNEXORIS SYSTEM | نظام NNEXORIS لأتمتة محطات الوقود" in html
    assert token.public_id not in html
    assert "raw HEX" not in html
    with app.app_context():
        from app.customer_management.qr_security import decrypt_qr_token
        raw_token = decrypt_qr_token(ciphertext)
    resolved = client.post("/api/v1/customer/qr/resolve", json={"token": raw_token}, headers=auth)
    assert resolved.status_code == 200 and resolved.get_json()["valid"] is True
    disabled = client.post(f"/self-service/customer-management/qr/{token_id}/disable")
    assert disabled.status_code == 302
    rejected = client.post("/api/v1/customer/qr/resolve", json={"token": raw_token}, headers=auth)
    assert rejected.get_json()["valid"] is False
