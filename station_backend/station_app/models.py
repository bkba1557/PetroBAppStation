from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base, utcnow


class StationAppEmployee(Base):
    __tablename__ = "station_app_employees"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    public_id: Mapped[str] = mapped_column(String(36), nullable=False, unique=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False
    )
    station_id: Mapped[int] = mapped_column(
        ForeignKey("stations.id", ondelete="RESTRICT"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    password_lookup_digest: Mapped[str] = mapped_column(
        String(64), nullable=False, unique=True
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    failed_login_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("unified_users.id", ondelete="SET NULL")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow
    )

    __table_args__ = (
        Index("ix_station_app_employee_station", "station_id", "enabled"),
        Index("ix_station_app_employee_company", "company_id"),
    )


class StationAppSession(Base):
    __tablename__ = "station_app_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[str] = mapped_column(String(96), nullable=False, unique=True)
    employee_id: Mapped[int] = mapped_column(
        ForeignKey("station_app_employees.id", ondelete="CASCADE"), nullable=False
    )
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    ip_address: Mapped[str | None] = mapped_column(String(80))
    user_agent: Mapped[str | None] = mapped_column(String(500))
    issued_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoke_reason: Mapped[str | None] = mapped_column(String(80))

    __table_args__ = (
        Index("ix_station_app_session_employee", "employee_id", "expires_at"),
    )


class StationAppQrResolution(Base):
    __tablename__ = "station_app_qr_resolutions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    public_id: Mapped[str] = mapped_column(String(36), nullable=False, unique=True)
    employee_id: Mapped[int] = mapped_column(
        ForeignKey("station_app_employees.id", ondelete="CASCADE"), nullable=False
    )
    qr_token_id: Mapped[int] = mapped_column(
        ForeignKey("customer_qr_tokens.id", ondelete="RESTRICT"), nullable=False
    )
    station_id: Mapped[int] = mapped_column(
        ForeignKey("stations.id", ondelete="RESTRICT"), nullable=False
    )
    pump_id: Mapped[int] = mapped_column(
        ForeignKey("pumps.id", ondelete="RESTRICT"), nullable=False
    )
    nozzle_id: Mapped[int] = mapped_column(
        ForeignKey("nozzles.id", ondelete="RESTRICT"), nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )

    __table_args__ = (
        Index("ix_station_app_qr_employee", "employee_id", "expires_at"),
    )


class StationAppFuelingSession(Base):
    __tablename__ = "station_app_fueling_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    public_id: Mapped[str] = mapped_column(String(36), nullable=False, unique=True)
    idempotency_key: Mapped[str] = mapped_column(String(190), nullable=False, unique=True)
    employee_id: Mapped[int] = mapped_column(
        ForeignKey("station_app_employees.id", ondelete="RESTRICT"), nullable=False
    )
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False
    )
    station_id: Mapped[int] = mapped_column(
        ForeignKey("stations.id", ondelete="RESTRICT"), nullable=False
    )
    shift_id: Mapped[int] = mapped_column(
        ForeignKey("shift_sessions.id", ondelete="RESTRICT"), nullable=False
    )
    pump_id: Mapped[int] = mapped_column(
        ForeignKey("pumps.id", ondelete="RESTRICT"), nullable=False
    )
    nozzle_id: Mapped[int] = mapped_column(
        ForeignKey("nozzles.id", ondelete="RESTRICT"), nullable=False
    )
    qr_resolution_id: Mapped[int] = mapped_column(
        ForeignKey("station_app_qr_resolutions.id", ondelete="RESTRICT"), nullable=False
    )
    delivery_id: Mapped[str | None] = mapped_column(String(80), unique=True)
    cancellation_delivery_id: Mapped[str | None] = mapped_column(
        String(80), unique=True
    )
    sale_transaction_id: Mapped[int | None] = mapped_column(
        ForeignKey("sale_transactions.id", ondelete="SET NULL"), unique=True
    )
    requested_amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    fueling_mode: Mapped[str] = mapped_column(
        String(20), nullable=False, default="PRESET"
    )
    actual_amount: Mapped[float | None] = mapped_column(Numeric(14, 2))
    actual_liters: Mapped[float | None] = mapped_column(Numeric(14, 3))
    unit_price: Mapped[float] = mapped_column(Numeric(12, 3), nullable=False)
    fuel_code: Mapped[str] = mapped_column(String(40), nullable=False)
    status: Mapped[str] = mapped_column(
        String(40), nullable=False, default="AUTHORIZATION_QUEUED"
    )
    payment_method: Mapped[str | None] = mapped_column(String(20))
    payment_other_reason: Mapped[str | None] = mapped_column(Text)
    payment_recorded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    authorized_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    fueling_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cancel_requested_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    failure_code: Mapped[str | None] = mapped_column(String(100))
    failure_message: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow
    )

    __table_args__ = (
        Index("ix_station_app_fueling_employee", "employee_id", "created_at"),
        Index("ix_station_app_fueling_station", "station_id", "created_at"),
        Index(
            "uq_station_app_active_nozzle",
            "station_id",
            "pump_id",
            "nozzle_id",
            unique=True,
            postgresql_where=text(
                "status IN ('AUTHORIZATION_QUEUED','EDGE_RECEIVED','PUMP_WAITING',"
                "'PUMP_AUTHORIZED','FUELING','COMPLETED_AWAITING_PAYMENT',"
                "'CANCELLATION_QUEUED','CANCELLATION_FAILED')"
            ),
        ),
    )


class StationAppAuditEvent(Base):
    __tablename__ = "station_app_audit_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    employee_id: Mapped[int | None] = mapped_column(
        ForeignKey("station_app_employees.id", ondelete="SET NULL")
    )
    company_id: Mapped[int | None] = mapped_column(
        ForeignKey("companies.id", ondelete="SET NULL")
    )
    station_id: Mapped[int | None] = mapped_column(
        ForeignKey("stations.id", ondelete="SET NULL")
    )
    fueling_session_id: Mapped[int | None] = mapped_column(
        ForeignKey("station_app_fueling_sessions.id", ondelete="SET NULL")
    )
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    correlation_id: Mapped[str] = mapped_column(String(64), nullable=False)
    ip_address: Mapped[str | None] = mapped_column(String(80))
    details_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )

    __table_args__ = (
        Index("ix_station_app_audit_employee", "employee_id", "created_at"),
    )
