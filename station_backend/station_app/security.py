import base64
import hashlib
import hmac
import json
import secrets
import time
from datetime import timedelta, timezone
from functools import wraps

from flask import current_app, g, jsonify, request
from sqlalchemy import select
from werkzeug.security import check_password_hash, generate_password_hash

from app.models import utcnow

from .models import StationAppEmployee, StationAppSession


SESSION_HOURS = 13


def _b64encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _b64decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def password_lookup_digest(password: str) -> str:
    return hmac.new(
        current_app.config["PASSWORD_PEPPER"].encode(),
        password.encode(),
        hashlib.sha256,
    ).hexdigest()


def password_hash(password: str) -> str:
    return generate_password_hash(password, method="scrypt")


def password_valid(stored: str, supplied: str) -> bool:
    return check_password_hash(stored, supplied)


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _jwt_encode(payload: dict) -> str:
    header = _b64encode(
        json.dumps({"alg": "HS256", "typ": "JWT"}, separators=(",", ":")).encode()
    )
    body = _b64encode(
        json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
    )
    message = f"{header}.{body}".encode()
    signature = hmac.new(
        current_app.config["JWT_SECRET"].encode(), message, hashlib.sha256
    ).digest()
    return f"{header}.{body}.{_b64encode(signature)}"


def _jwt_decode(token: str) -> dict:
    try:
        header, body, signature = token.split(".")
        message = f"{header}.{body}".encode()
        expected = hmac.new(
            current_app.config["JWT_SECRET"].encode(), message, hashlib.sha256
        ).digest()
        if not hmac.compare_digest(expected, _b64decode(signature)):
            raise ValueError
        payload = json.loads(_b64decode(body))
        if payload.get("typ") != "station_employee" or int(
            payload.get("exp", 0)
        ) <= int(time.time()):
            raise ValueError
        return payload
    except (ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
        raise ValueError("INVALID_OR_EXPIRED_TOKEN") from exc


def issue_session(db, employee: StationAppEmployee) -> tuple[str, StationAppSession]:
    now = utcnow()
    expires_at = now + timedelta(hours=SESSION_HOURS)
    session_id = secrets.token_urlsafe(48)
    claims = {
        "sub": employee.public_id,
        "sid": session_id,
        "typ": "station_employee",
        "iat": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
    }
    token = _jwt_encode(claims)
    row = StationAppSession(
        session_id=session_id,
        employee_id=employee.id,
        token_hash=token_hash(token),
        ip_address=(
            request.headers.get("X-Forwarded-For") or request.remote_addr or ""
        )[:80],
        user_agent=(request.user_agent.string or "")[:500],
        issued_at=now,
        expires_at=expires_at,
    )
    db.add(row)
    return token, row


def employee_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        authorization = request.headers.get("Authorization", "")
        if not authorization.startswith("Bearer "):
            return jsonify(error="AUTHENTICATION_REQUIRED"), 401
        raw_token = authorization[7:]
        try:
            claims = _jwt_decode(raw_token)
        except ValueError as exc:
            return jsonify(error=str(exc)), 401
        db = g.db
        session_row = db.scalar(
            select(StationAppSession).where(
                StationAppSession.session_id == claims["sid"],
                StationAppSession.token_hash == token_hash(raw_token),
            )
        )
        employee = db.scalar(
            select(StationAppEmployee).where(
                StationAppEmployee.public_id == claims["sub"]
            )
        )
        now = utcnow()
        if (
            session_row is None
            or employee is None
            or not employee.enabled
            or session_row.revoked_at is not None
            or _expired(session_row.expires_at, now)
        ):
            return jsonify(error="SESSION_EXPIRED"), 401
        session_row.last_used_at = now
        g.employee = employee
        g.employee_session = session_row
        return view(*args, **kwargs)

    return wrapped


def internal_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        supplied = request.headers.get("X-Station-Internal-Token", "")
        expected = current_app.config["INTERNAL_TOKEN"]
        if not supplied or not hmac.compare_digest(supplied, expected):
            return jsonify(error="INTERNAL_AUTHENTICATION_REQUIRED"), 401
        return view(*args, **kwargs)

    return wrapped


def _expired(value, now) -> bool:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value <= now

