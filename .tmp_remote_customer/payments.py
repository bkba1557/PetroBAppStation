import hashlib
import hmac
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from decimal import Decimal
import secrets
import httpx
from datetime import datetime, timezone
from flask import render_template, abort

from flask import current_app, g, jsonify, request
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.extensions import get_session
from app.models import (
    CustomerAuditEvent, CustomerPaymentIntent, CustomerWallet, PaymentWebhookEvent,
    WalletTransaction, utcnow,
)

from . import customer_api
from .common import api_error, emit
from .security import customer_required


def moyasar_checkout_token(topup_id, customer_id):
    message = f"{topup_id}:{customer_id}".encode()
    return hmac.new(current_app.config["CUSTOMER_JWT_SECRET"].encode(), message, hashlib.sha256).hexdigest()


def _valid_moyasar_checkout_token(topup_id, customer_id, supplied):
    expected = moyasar_checkout_token(topup_id, customer_id)
    return bool(supplied and hmac.compare_digest(expected, str(supplied)))


def _moyasar_get(payment_id):
    secret = current_app.config.get("MOYASAR_SECRET_KEY", "")
    if not secret or not payment_id or payment_id.startswith("moyasar_pending_"):
        return None
    try:
        with httpx.Client(verify=True, timeout=15, trust_env=False, follow_redirects=False, http1=True) as client:
            response = client.get(f"https://api.moyasar.com/v1/payments/{payment_id}", auth=(secret, ""), headers={"Accept":"application/json"})
        payload = response.json() if response.content else {}
        return payload if isinstance(payload, dict) and response.status_code == 200 else None
    except (httpx.HTTPError, ValueError):
        return None


@customer_api.get("/wallet/topups/<topup_id>/checkout")
def moyasar_checkout(topup_id):
    db = get_session()
    intent = db.scalar(select(CustomerPaymentIntent).where(CustomerPaymentIntent.public_id == topup_id))
    token = request.args.get("token", "")
    if intent is None or intent.status != "pendingPayment" or not _valid_moyasar_checkout_token(topup_id, intent.customer_id, token):
        abort(404)
    return render_template("customer/moyasar_checkout.html", topup=intent,
                           publishable_key=current_app.config.get("MOYASAR_PUBLISHABLE_KEY", ""),
                           token=token)


@customer_api.post("/wallet/topups/<topup_id>/complete")
def moyasar_complete(topup_id):
    db = get_session(); data = request.get_json(silent=True) or {}
    intent = db.scalar(select(CustomerPaymentIntent).where(CustomerPaymentIntent.public_id == topup_id).with_for_update())
    if intent is None or not _valid_moyasar_checkout_token(topup_id, intent.customer_id, data.get("token")):
        return api_error("TOPUP_NOT_FOUND", 404)
    if intent.status == "paid":
        return jsonify({"status":"paid", "id":topup_id})
    payment_id = str(data.get("payment_id") or "")
    payment = _moyasar_get(payment_id)
    if not payment:
        return api_error("PAYMENT_NOT_FOUND", 404)
    metadata = payment.get("metadata") if isinstance(payment.get("metadata"), dict) else {}
    if str(metadata.get("topup_id") or "") != topup_id:
        return api_error("PAYMENT_TOPUP_MISMATCH", 409)
    expected_minor = int(Decimal(str(intent.amount)) * 100)
    if int(payment.get("amount") or 0) != expected_minor or str(payment.get("currency", "")).upper() != "SAR":
        intent.failure_code = "PAYMENT_AMOUNT_MISMATCH"; db.commit(); return api_error("PAYMENT_AMOUNT_MISMATCH", 409)
    intent.provider_payment_intent_id = payment_id
    status = str(payment.get("status") or "")
    if status != "paid":
        intent.status = "failed" if status in {"failed", "refunded", "voided"} else "pendingPayment"
        intent.failure_code = status[:100] or "PAYMENT_PENDING"
        db.commit(); return jsonify({"status": intent.status, "id": topup_id})
    wallet = db.scalar(select(CustomerWallet).where(CustomerWallet.id == intent.wallet_id).with_for_update())
    amount = Decimal(str(intent.amount)); before = Decimal(str(wallet.balance)) - Decimal(str(wallet.reserved_balance))
    wallet.balance = Decimal(str(wallet.balance)) + amount; wallet.version += 1
    db.add(WalletTransaction(company_id=intent.company_id, wallet_id=wallet.id, transaction_type="TOPUP_CREDIT", amount=amount,
        balance_before=before, balance_after=before + amount, reference=f"moyasar:{payment_id}", idempotency_key=f"moyasar:{payment_id}", metadata_json={"provider":"moyasar"}))
    intent.status = "paid"; intent.paid_at = utcnow(); intent.failure_code = None
    emit(intent.customer_id, "TOPUP_SUCCEEDED", entity_id=intent.public_id, version=wallet.version, payload={"topupId": intent.public_id, "walletVersion": wallet.version})
    db.commit(); return jsonify({"status":"paid", "id":topup_id})


def create_stripe_payment_intent(*, amount_minor, currency, idempotency_key, metadata):
    body = {"amount": str(amount_minor), "currency": currency,
            "automatic_payment_methods[enabled]": "true"}
    for key, value in metadata.items():
        body[f"metadata[{key}]"] = value
    req = urllib.request.Request("https://api.stripe.com/v1/payment_intents",
        data=urllib.parse.urlencode(body).encode(), method="POST",
        headers={"Authorization": f"Bearer {current_app.config['STRIPE_SECRET_KEY']}",
                 "Idempotency-Key": idempotency_key,
                 "Content-Type": "application/x-www-form-urlencoded"})
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            payload = json.loads(response.read())
    except (urllib.error.URLError, json.JSONDecodeError) as exc:
        raise RuntimeError("Stripe request failed") from exc
    if not payload.get("id") or not payload.get("client_secret"):
        raise RuntimeError("Stripe returned an incomplete PaymentIntent")
    return payload


def _verified_stripe_event(raw, signature):
    secret = current_app.config["STRIPE_WEBHOOK_SECRET"]
    if not secret:
        raise ValueError("STRIPE_WEBHOOK_NOT_CONFIGURED")
    parts = {}
    for item in signature.split(","):
        if "=" in item:
            key, value = item.split("=", 1); parts.setdefault(key, []).append(value)
    try:
        timestamp = int(parts["t"][0])
    except (KeyError, ValueError, IndexError):
        raise ValueError("INVALID_STRIPE_SIGNATURE")
    if abs(int(time.time()) - timestamp) > 300:
        raise ValueError("STRIPE_SIGNATURE_EXPIRED")
    expected = hmac.new(secret.encode(), str(timestamp).encode() + b"." + raw, hashlib.sha256).hexdigest()
    if not any(hmac.compare_digest(expected, candidate) for candidate in parts.get("v1", [])):
        raise ValueError("INVALID_STRIPE_SIGNATURE")
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError("INVALID_STRIPE_PAYLOAD") from exc


@customer_api.post("/payments/stripe/webhook")
def stripe_webhook():
    raw = request.get_data(cache=False)
    try:
        event = _verified_stripe_event(raw, request.headers.get("Stripe-Signature", ""))
    except ValueError as exc:
        return api_error(str(exc), 400)
    event_id = str(event.get("id") or "")
    event_type = str(event.get("type") or "")
    stripe_object = ((event.get("data") or {}).get("object") or {})
    provider_id = str(stripe_object.get("id") or "")
    if not event_id or not provider_id:
        return api_error("INVALID_STRIPE_EVENT", 400)
    db = get_session()
    intent = db.scalar(select(CustomerPaymentIntent).where(
        CustomerPaymentIntent.provider_payment_intent_id == provider_id
    ).with_for_update())
    if intent is None:
        return api_error("PAYMENT_INTENT_NOT_FOUND", 404)
    existing = db.scalar(select(PaymentWebhookEvent).where(
        PaymentWebhookEvent.gateway_id == intent.gateway_id,
        PaymentWebhookEvent.provider_event_id == event_id,
    ))
    if existing:
        return jsonify(received=True, duplicate=True)
    webhook = PaymentWebhookEvent(gateway_id=intent.gateway_id,
        provider_event_id=event_id, signature_valid=True, event_type=event_type,
        payload_json={"id": event_id, "type": event_type, "object_id": provider_id},
        status="received")
    db.add(webhook)
    if event_type == "payment_intent.succeeded":
        expected_minor = int(Decimal(str(intent.amount)) * 100)
        if int(stripe_object.get("amount_received") or 0) != expected_minor or str(stripe_object.get("currency")) != "sar":
            webhook.status = "rejected"; webhook.error_message = "PAYMENT_AMOUNT_MISMATCH"
            db.commit(); return api_error("PAYMENT_AMOUNT_MISMATCH", 409)
        wallet = db.scalar(select(CustomerWallet).where(
            CustomerWallet.id == intent.wallet_id).with_for_update())
        if intent.status != "paid":
            amount = Decimal(str(intent.amount)); before = Decimal(str(wallet.balance)) - Decimal(str(wallet.reserved_balance))
            wallet.balance = Decimal(str(wallet.balance)) + amount
            wallet.version += 1
            db.add(WalletTransaction(company_id=intent.company_id, wallet_id=wallet.id,
                transaction_type="TOPUP_CREDIT", amount=amount, balance_before=before,
                balance_after=before + amount, reference=f"stripe:{provider_id}",
                idempotency_key=f"stripe:{provider_id}", metadata_json={"stripe_event_id": event_id}))
            intent.status = "paid"; intent.paid_at = utcnow()
            emit(intent.customer_id, "TOPUP_SUCCEEDED", entity_id=intent.public_id,
                 version=wallet.version, payload={"topupId": intent.public_id, "walletVersion": wallet.version})
            emit(intent.customer_id, "WALLET_UPDATED", entity_id=str(wallet.id),
                 version=wallet.version, payload={"walletVersion": wallet.version})
            db.add(CustomerAuditEvent(customer_id=intent.customer_id, company_id=intent.company_id,
                correlation_id=request.headers.get("X-Correlation-Id", "")[:64] or event_id,
                action="WALLET_TOPUP_SUCCEEDED", entity_type="payment_intent", entity_id=intent.public_id,
                ip_address=(request.headers.get("X-Forwarded-For") or request.remote_addr or "")[:80],
                details_json={"amount": str(intent.amount), "currency": intent.currency}, source="STRIPE_WEBHOOK"))
        webhook.status = "processed"; webhook.processed_at = utcnow()
    elif event_type == "payment_intent.payment_failed":
        intent.status = "failed"; intent.failure_code = str(stripe_object.get("last_payment_error") or "PAYMENT_FAILED")[:100]
        webhook.status = "processed"; webhook.processed_at = utcnow()
        emit(intent.customer_id, "TOPUP_FAILED", entity_id=intent.public_id,
             payload={"topupId": intent.public_id})
        db.add(CustomerAuditEvent(customer_id=intent.customer_id, company_id=intent.company_id,
            correlation_id=request.headers.get("X-Correlation-Id", "")[:64] or event_id,
            action="WALLET_TOPUP_FAILED", entity_type="payment_intent", entity_id=intent.public_id,
            ip_address=(request.headers.get("X-Forwarded-For") or request.remote_addr or "")[:80],
            details_json={"failure": "PAYMENT_FAILED"}, source="STRIPE_WEBHOOK"))
    else:
        webhook.status = "ignored"; webhook.processed_at = utcnow()
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        duplicate = db.scalar(select(PaymentWebhookEvent).where(
            PaymentWebhookEvent.gateway_id == intent.gateway_id,
            PaymentWebhookEvent.provider_event_id == event_id,
        ))
        if duplicate is not None:
            return jsonify(received=True, duplicate=True)
        raise
    return jsonify(received=True, duplicate=False)
