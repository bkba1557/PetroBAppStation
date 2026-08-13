import hashlib
import hmac
from decimal import Decimal, InvalidOperation
from uuid import uuid4

from flask import current_app, g, jsonify, request, url_for
from sqlalchemy import case, func, select
from sqlalchemy.exc import IntegrityError

from app.extensions import get_session
from app.models import CustomerPaymentIntent, CustomerWallet, PaymentGateway, WalletTransaction

from . import customer_api
from .common import api_error, audit
from .payments import moyasar_checkout_token
from .security import customer_required


def wallet_for_customer(db, *, lock=False):
    query = select(CustomerWallet).where(CustomerWallet.customer_id == g.customer.id)
    return db.scalar(query.with_for_update() if lock else query)


def wallet_json(row):
    available = Decimal(str(row.balance)) - Decimal(str(row.reserved_balance))
    credited, spent, refunded = get_session().execute(select(
        func.coalesce(func.sum(case((WalletTransaction.transaction_type == "TOPUP_CREDIT", WalletTransaction.amount), else_=0)), 0),
        func.coalesce(func.sum(case((WalletTransaction.transaction_type == "FUELING_CAPTURE", -WalletTransaction.amount), else_=0)), 0),
        func.coalesce(func.sum(case((WalletTransaction.transaction_type == "REFUND", WalletTransaction.amount), else_=0)), 0),
    ).where(WalletTransaction.wallet_id == row.id)).one()
    return {"id": str(row.id), "balance": {"available": float(available),
        "reserved": float(row.reserved_balance), "currency": row.currency,
        "version": row.version}, "summary": {"totalCredited": float(credited),
        "totalSpent": float(spent), "totalRefunded": float(refunded)},
        "updatedAt": row.updated_at.isoformat()}


def topup_json(row, *, client_secret=None, publishable_key=None):
    result = {"id": row.public_id, "amount": float(row.amount), "status": row.status,
              "paymentRedirectUrl": None}
    if client_secret:
        result["clientSecret"] = client_secret
        result["publishableKey"] = publishable_key
        result["paymentIntentId"] = row.provider_payment_intent_id
    if row.status == "pendingPayment":
        checkout_token = moyasar_checkout_token(row.public_id, row.customer_id)
        result["checkoutToken"] = checkout_token
        result["paymentRedirectUrl"] = url_for("customer_api.moyasar_checkout", topup_id=row.public_id,
            token=checkout_token, _external=True)
        result["publishableKey"] = current_app.config.get("MOYASAR_PUBLISHABLE_KEY")
    return result


@customer_api.get("/wallet")
@customer_required
def wallet_get():
    row = wallet_for_customer(get_session())
    if row is None:
        return api_error("WALLET_NOT_FOUND", 404)
    return jsonify(wallet_json(row))


@customer_api.get("/wallet/transactions")
@customer_required
def wallet_transactions():
    db = get_session(); wallet = wallet_for_customer(db)
    if wallet is None:
        return api_error("WALLET_NOT_FOUND", 404)
    rows = db.scalars(select(WalletTransaction).where(
        WalletTransaction.wallet_id == wallet.id
    ).order_by(WalletTransaction.id.desc()).limit(100)).all()
    return jsonify([{"id": str(row.id), "type": row.transaction_type,
        "amount": float(row.amount), "currency": wallet.currency,
        "createdAt": row.created_at.isoformat()} for row in rows])


@customer_api.post("/wallet/topups")
@customer_required
def wallet_topup():
    db = get_session(); data = request.get_json(silent=True) or {}
    idempotency_key = (request.headers.get("Idempotency-Key") or "")[:190]
    if not idempotency_key:
        return api_error("IDEMPOTENCY_KEY_REQUIRED", 400)
    existing = db.scalar(select(CustomerPaymentIntent).where(
        CustomerPaymentIntent.idempotency_key == idempotency_key,
        CustomerPaymentIntent.customer_id == g.customer.id,
    ))
    if existing:
        return jsonify(topup_json(existing))
    try:
        amount = Decimal(str(data.get("amount"))).quantize(Decimal("0.01"))
    except (InvalidOperation, TypeError):
        return api_error("INVALID_TOPUP_AMOUNT", 400)
    if amount < Decimal("1.00") or amount > Decimal("5000.00"):
        return api_error("TOPUP_AMOUNT_OUT_OF_RANGE", 400)
    if not current_app.config.get("MOYASAR_SECRET_KEY") or not current_app.config.get("MOYASAR_PUBLISHABLE_KEY"):
        return api_error("MOYASAR_NOT_CONFIGURED", 503)
    wallet = wallet_for_customer(db, lock=True)
    gateway = db.scalar(select(PaymentGateway).where(
        PaymentGateway.company_id == g.customer.company_id,
        PaymentGateway.provider == "moyasar", PaymentGateway.environment == current_app.config.get("MOYASAR_MODE", "live"),
    ))
    if gateway is None:
        gateway = PaymentGateway(company_id=g.customer.company_id, provider="moyasar",
            display_name="Moyasar Customer Wallet", environment=current_app.config.get("MOYASAR_MODE", "live"), enabled=True,
            currency="SAR", country="SA", integration_type="hosted_moyasar",
            auth_type="secret_key", allowed_domains=["api.stripe.com"], configuration_json={})
        db.add(gateway); db.flush()
    row = CustomerPaymentIntent(public_id=str(__import__("uuid").uuid4()),
        company_id=g.customer.company_id, customer_id=g.customer.id, wallet_id=wallet.id,
        gateway_id=gateway.id, idempotency_key=idempotency_key,
        provider_payment_intent_id=f"moyasar_pending_{uuid4().hex}", amount=amount, currency="SAR",
        status="pendingPayment")
    db.add(row)
    try:
        db.flush()
        audit("WALLET_TOPUP_CREATED", entity_type="payment_intent", entity_id=row.public_id,
              details={"amount": str(amount), "currency": "SAR"})
        db.commit()
    except IntegrityError:
        db.rollback()
        existing = db.scalar(select(CustomerPaymentIntent).where(
            CustomerPaymentIntent.idempotency_key == idempotency_key,
            CustomerPaymentIntent.customer_id == g.customer.id,
        ))
        if existing is not None:
            return jsonify(topup_json(existing))
        raise
    return jsonify(topup_json(row)), 201


@customer_api.get("/wallet/topups/<topup_id>")
@customer_required
def wallet_topup_get(topup_id):
    row = get_session().scalar(select(CustomerPaymentIntent).where(
        CustomerPaymentIntent.public_id == topup_id,
        CustomerPaymentIntent.customer_id == g.customer.id,
    ))
    if row is None:
        return api_error("TOPUP_NOT_FOUND", 404)
    return jsonify(topup_json(row))
