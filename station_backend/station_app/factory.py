import os
import sys

from flask import Flask, g
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def _required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"{name} is required")
    return value


def _required_any(*names: str) -> str:
    for name in names:
        value = os.getenv(name, "").strip()
        if value:
            return value
    raise RuntimeError(f"One of {', '.join(names)} is required")


def create_app():
    cloud_path = os.getenv("NNEXORIS_CLOUD_PATH", "/opt/nnexoris-cloud")
    if cloud_path not in sys.path:
        sys.path.insert(0, cloud_path)

    from .api import api

    app = Flask(__name__)
    app.config.update(
        DATABASE_URL=os.getenv("STATION_DATABASE_URL")
        or _required("PETROB_DATABASE_URL"),
        JWT_SECRET=_required("STATION_APP_JWT_SECRET"),
        PASSWORD_PEPPER=_required("STATION_APP_PASSWORD_PEPPER"),
        INTERNAL_TOKEN=_required("STATION_APP_INTERNAL_TOKEN"),
        CONFIG_SIGNING_PRIVATE_KEY_FILE=_required_any(
            "NNEXORIS_CONFIG_SIGNING_PRIVATE_KEY_FILE",
            "CONFIG_SIGNING_PRIVATE_KEY_FILE",
        ),
        CONFIG_SIGNING_PUBLIC_KEY_FILE=_required_any(
            "NNEXORIS_CONFIG_SIGNING_PUBLIC_KEY_FILE",
            "CONFIG_SIGNING_PUBLIC_KEY_FILE",
        ),
        CONFIG_SIGNING_KEY_ID=_required_any(
            "NNEXORIS_CONFIG_SIGNING_KEY_ID",
            "CONFIG_SIGNING_KEY_ID",
        ),
        MAX_FUELING_AMOUNT=DecimalEnv("STATION_APP_MAX_FUELING_AMOUNT", "5000"),
        JSON_AS_ASCII=False,
    )
    engine = create_engine(app.config["DATABASE_URL"], pool_pre_ping=True)
    factory = sessionmaker(bind=engine, expire_on_commit=False)

    @app.before_request
    def open_session():
        g.db = factory()

    @app.teardown_request
    def close_session(error=None):
        db = g.pop("db", None)
        if db is not None:
            if error is not None:
                db.rollback()
            db.close()

    @app.after_request
    def security_headers(response):
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        return response

    app.register_blueprint(api)
    return app


def DecimalEnv(name: str, default: str):
    from decimal import Decimal

    return Decimal(os.getenv(name, default))
