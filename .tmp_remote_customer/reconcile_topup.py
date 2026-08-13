import os
import sys
sys.path.insert(0, "/opt/nnexoris-cloud")
import httpx
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4
from app import create_app
from app.extensions import get_session
from app.models import CustomerPaymentIntent, CustomerWallet, WalletTransaction, CustomerRealtimeEvent, CustomerAuditEvent, utcnow
from sqlalchemy import select

app = create_app()
with app.app_context():
    db = get_session()
    intent = db.scalar(select(CustomerPaymentIntent).where(CustomerPaymentIntent.id == 31).with_for_update())
    if not intent or intent.status == "paid":
        print("RECONCILIATION already_paid_or_missing")
        raise SystemExit
    secret = os.getenv("MOYASAR_SECRET_KEY", "")
    with httpx.Client(timeout=15, verify=True, trust_env=False) as client:
        payload = client.get("https://api.moyasar.com/v1/payments", auth=(secret, ""), params={"limit": 20}, headers={"Accept": "application/json"}).json()
    rows = payload.get("payments", payload) if isinstance(payload, dict) else payload
    expected_minor = int(Decimal(str(intent.amount)) * 100)
    candidates = []
    for payment in rows if isinstance(rows, list) else []:
        if payment.get("status") != "paid" or int(payment.get("amount") or 0) != expected_minor or str(payment.get("currency", "")).upper() != "SAR":
            continue
        try:
            created = datetime.fromisoformat(str(payment.get("created_at")).replace("Z", "+00:00"))
        except Exception:
            continue
        base = intent.created_at.replace(tzinfo=timezone.utc) if intent.created_at.tzinfo is None else intent.created_at
        if abs((created - base).total_seconds()) <= 120:
            candidates.append(payment)
    if len(candidates) != 1:
        print("RECONCILIATION not_applied_candidates", len(candidates))
        raise SystemExit
    payment = candidates[0]
    wallet = db.scalar(select(CustomerWallet).where(CustomerWallet.id == intent.wallet_id).with_for_update())
    reference = f"moyasar:{payment.get('id')}"
    existing = db.scalar(select(WalletTransaction).where(WalletTransaction.wallet_id == wallet.id, WalletTransaction.reference == reference, WalletTransaction.transaction_type == "TOPUP_CREDIT"))
    if existing:
        intent.status = "paid"
        intent.provider_payment_intent_id = str(payment.get("id"))
        intent.paid_at = utcnow()
        intent.failure_code = None
    else:
        amount = Decimal(str(intent.amount))
        before = Decimal(str(wallet.balance)) - Decimal(str(wallet.reserved_balance))
        wallet.balance = Decimal(str(wallet.balance)) + amount
        wallet.version += 1
        db.add(WalletTransaction(company_id=intent.company_id, wallet_id=wallet.id, transaction_type="TOPUP_CREDIT", amount=amount, balance_before=before, balance_after=before + amount, reference=reference, idempotency_key=reference, metadata_json={"provider": "moyasar", "reconciled": True}))
        intent.status = "paid"
        intent.provider_payment_intent_id = str(payment.get("id"))
        intent.paid_at = utcnow()
        intent.failure_code = None
        db.add(CustomerRealtimeEvent(customer_id=intent.customer_id, event_type="TOPUP_SUCCEEDED", entity_id=intent.public_id, event_version=wallet.version, payload_json={"topupId": intent.public_id, "walletVersion": wallet.version}))
        db.add(CustomerAuditEvent(customer_id=intent.customer_id, company_id=intent.company_id, correlation_id=str(uuid4()), action="WALLET_TOPUP_RECONCILED", entity_type="payment_intent", entity_id=intent.public_id, details_json={"amount": str(intent.amount), "provider": "moyasar"}, source="CUSTOMER_APP"))
    db.commit()
    print("RECONCILIATION applied amount", intent.amount, "status", intent.status)
