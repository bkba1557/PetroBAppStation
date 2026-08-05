from datetime import datetime, timezone

from sqlalchemy import BigInteger, Boolean, DateTime, Float, ForeignKey, ForeignKeyConstraint, Index, Integer, JSON, Numeric, String, Text, UniqueConstraint, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utcnow():
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)


class Company(TimestampMixin, Base):
    __tablename__ = "companies"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_key: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    name_ar: Mapped[str] = mapped_column(String(160), nullable=False)
    name_en: Mapped[str] = mapped_column(String(160), nullable=False)
    company_type: Mapped[str] = mapped_column(String(24), nullable=False, default="franchise")
    short_name: Mapped[str | None] = mapped_column(String(80))
    commercial_registration_number: Mapped[str | None] = mapped_column(String(80), unique=True)
    address: Mapped[str | None] = mapped_column(Text)
    location_url: Mapped[str | None] = mapped_column(String(500))
    industry_code: Mapped[str | None] = mapped_column(String(60))
    industry_other: Mapped[str | None] = mapped_column(String(160))
    responsible_name: Mapped[str | None] = mapped_column(String(160))
    responsible_job_title: Mapped[str | None] = mapped_column(String(120))
    responsible_mobile: Mapped[str | None] = mapped_column(String(40))
    responsible_email: Mapped[str | None] = mapped_column(String(255))
    lifecycle_status: Mapped[str] = mapped_column(String(24), default="ACTIVE", nullable=False)
    user_limit: Mapped[int | None] = mapped_column(Integer, default=10)
    company_admin_counts_toward_quota: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    preferences_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    last_activity_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    logo: Mapped[str | None] = mapped_column(String(255))
    primary_color: Mapped[str] = mapped_column(String(20), default="#138bb8", nullable=False)
    secondary_color: Mapped[str] = mapped_column(String(20), default="#31d89a", nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    customer_self_service_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Station(TimestampMixin, Base):
    __tablename__ = "stations"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int | None] = mapped_column(ForeignKey("companies.id", ondelete="RESTRICT"))
    station_id: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    station_code: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    name_ar: Mapped[str] = mapped_column(String(160), nullable=False)
    name_en: Mapped[str] = mapped_column(String(160), nullable=False)
    company_name: Mapped[str | None] = mapped_column(String(160))
    branch_name: Mapped[str | None] = mapped_column(String(160))
    city: Mapped[str | None] = mapped_column(String(100))
    region: Mapped[str | None] = mapped_column(String(100))
    address: Mapped[str | None] = mapped_column(Text)
    domain: Mapped[str | None] = mapped_column(String(255))
    subdomain: Mapped[str | None] = mapped_column(String(120))
    timezone: Mapped[str] = mapped_column(String(80), nullable=False, default="Asia/Riyadh")
    logo: Mapped[str | None] = mapped_column(String(255))
    primary_color: Mapped[str] = mapped_column(String(20), default="#138bb8", nullable=False)
    secondary_color: Mapped[str] = mapped_column(String(20), default="#31d89a", nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)
    console_mode: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    customer_self_service_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    self_service_status: Mapped[str] = mapped_column(String(24), default="DISABLED", nullable=False)
    self_service_start_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    self_service_end_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    maximum_customer_amount: Mapped[float] = mapped_column(Numeric(14, 2), default=100, nullable=False)
    minimum_customer_amount: Mapped[float] = mapped_column(Numeric(14, 2), default=5, nullable=False)
    allowed_fuel_types: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    require_operator_confirmation: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    allow_wallet_payment: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    allow_stripe_direct_payment: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class StationSetting(TimestampMixin, Base):
    __tablename__ = "station_settings"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    station_id: Mapped[int] = mapped_column(ForeignKey("stations.id", ondelete="RESTRICT"), nullable=False)
    key: Mapped[str] = mapped_column(String(120), nullable=False)
    value: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    __table_args__ = (UniqueConstraint("station_id", "key", name="uq_station_setting"),)


class FuelProduct(TimestampMixin, Base):
    __tablename__ = "fuel_products"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    station_id: Mapped[int | None] = mapped_column(ForeignKey("stations.id", ondelete="RESTRICT"))
    code: Mapped[str] = mapped_column(String(40), nullable=False)
    name_ar: Mapped[str] = mapped_column(String(120), nullable=False)
    name_en: Mapped[str] = mapped_column(String(120), nullable=False)
    color: Mapped[str] = mapped_column(String(20), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    __table_args__ = (UniqueConstraint("station_id", "code", name="uq_fuel_product_station_code"),)


class ProtocolProfile(TimestampMixin, Base):
    __tablename__ = "protocol_profiles"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    station_id: Mapped[int | None] = mapped_column(ForeignKey("stations.id", ondelete="RESTRICT"))
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    code: Mapped[str | None] = mapped_column(String(100))
    device_category: Mapped[str] = mapped_column(String(40), nullable=False)
    vendor: Mapped[str] = mapped_column(String(80), nullable=False)
    driver: Mapped[str] = mapped_column(String(160), nullable=False)
    transport_type: Mapped[str] = mapped_column(String(40), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    description_ar: Mapped[str | None] = mapped_column(Text)
    description_en: Mapped[str | None] = mapped_column(Text)
    display_version: Mapped[str | None] = mapped_column(String(40))
    model_name: Mapped[str | None] = mapped_column(String(120))
    aliases_json: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    scope: Mapped[str] = mapped_column(String(40), default="MONITORING_ONLY", nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="DRAFT", nullable=False)
    is_builtin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_editable: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    schema_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    definition_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    published_version_id: Mapped[int | None] = mapped_column(Integer)
    created_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("unified_users.id", ondelete="SET NULL"))
    updated_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("unified_users.id", ondelete="SET NULL"))
    is_global: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    serial_port: Mapped[str | None] = mapped_column(String(160))
    baudrate: Mapped[int | None] = mapped_column(Integer)
    bytesize: Mapped[int | None] = mapped_column(Integer)
    parity: Mapped[str | None] = mapped_column(String(10))
    stopbits: Mapped[float | None] = mapped_column(Numeric(3, 1))
    host: Mapped[str | None] = mapped_column(String(255))
    port: Mapped[int | None] = mapped_column(Integer)
    timeout_seconds: Mapped[float] = mapped_column(Numeric(8, 3), default=1, nullable=False)
    poll_interval_seconds: Mapped[float] = mapped_column(Numeric(8, 3), default=1, nullable=False)
    command_templates: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    response_parser: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    checksum_type: Mapped[str | None] = mapped_column(String(80))
    retry_policy: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = (
        UniqueConstraint("station_id", "name", name="uq_protocol_station_name"),
        UniqueConstraint("code", name="uq_protocol_profile_code"),
        Index("ix_protocol_profile_catalog", "status", "device_category", "transport_type"),
    )


class ConnectionProfile(TimestampMixin, Base):
    __tablename__ = "connection_profiles"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    station_id: Mapped[int] = mapped_column(ForeignKey("stations.id", ondelete="RESTRICT"), nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    code: Mapped[str | None] = mapped_column(String(100))
    transport_type: Mapped[str] = mapped_column(String(40), nullable=False)
    connection_key: Mapped[str] = mapped_column(String(255), nullable=False)
    serial_port: Mapped[str | None] = mapped_column(String(160))
    baudrate: Mapped[int | None] = mapped_column(Integer)
    bytesize: Mapped[int | None] = mapped_column(Integer)
    parity: Mapped[str | None] = mapped_column(String(10))
    stopbits: Mapped[float | None] = mapped_column(Numeric(3, 1))
    flow_control: Mapped[str | None] = mapped_column(String(30))
    host: Mapped[str | None] = mapped_column(String(255))
    port: Mapped[int | None] = mapped_column(Integer)
    tcp_host: Mapped[str | None] = mapped_column(String(255))
    tcp_port: Mapped[int | None] = mapped_column(Integer)
    udp_host: Mapped[str | None] = mapped_column(String(255))
    udp_port: Mapped[int | None] = mapped_column(Integer)
    http_base_url: Mapped[str | None] = mapped_column(String(500))
    websocket_url: Mapped[str | None] = mapped_column(String(500))
    timeout_seconds: Mapped[float] = mapped_column(Numeric(8, 3), default=1, nullable=False)
    write_timeout_seconds: Mapped[float] = mapped_column(Numeric(8, 3), default=1, nullable=False)
    poll_interval_seconds: Mapped[float] = mapped_column(Numeric(8, 3), default=1, nullable=False)
    offline_after_seconds: Mapped[float] = mapped_column(Numeric(8, 3), default=10, nullable=False)
    retry_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    retry_delay_seconds: Mapped[float] = mapped_column(Numeric(8, 3), default=1, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    health_state: Mapped[str] = mapped_column(String(30), default="shadow", nullable=False)
    shadow_only: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_validation_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_connected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error: Mapped[str | None] = mapped_column(Text)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = (UniqueConstraint("station_id", "connection_key", name="uq_connection_station_key"),)


class Device(TimestampMixin, Base):
    __tablename__ = "devices"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    station_id: Mapped[int] = mapped_column(ForeignKey("stations.id", ondelete="RESTRICT"), nullable=False)
    device_id: Mapped[str] = mapped_column(String(100), nullable=False)
    device_category: Mapped[str] = mapped_column(String(40), nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    vendor: Mapped[str | None] = mapped_column(String(100))
    model: Mapped[str | None] = mapped_column(String(100))
    protocol_profile_id: Mapped[int | None] = mapped_column(ForeignKey("protocol_profiles.id", ondelete="RESTRICT"))
    connection_profile_id: Mapped[int | None] = mapped_column(ForeignKey("connection_profiles.id", ondelete="RESTRICT"))
    enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="unconfigured", nullable=False)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error: Mapped[str | None] = mapped_column(Text)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = (UniqueConstraint("station_id", "device_id", name="uq_device_station_id"), Index("ix_devices_station_category", "station_id", "device_category"))


class DeviceProtocolAssignment(TimestampMixin, Base):
    __tablename__ = "device_protocol_assignments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    device_id: Mapped[int | None] = mapped_column(ForeignKey("devices.id", ondelete="RESTRICT"))
    company_id: Mapped[int | None] = mapped_column(ForeignKey("companies.id", ondelete="RESTRICT"))
    edge_device_id: Mapped[int | None] = mapped_column(ForeignKey("edge_devices.id", ondelete="RESTRICT"))
    station_id: Mapped[int | None] = mapped_column(ForeignKey("stations.id", ondelete="RESTRICT"))
    device_category: Mapped[str | None] = mapped_column(String(40))
    device_record_id: Mapped[int | None] = mapped_column(Integer)
    protocol_profile_id: Mapped[int] = mapped_column(ForeignKey("protocol_profiles.id", ondelete="RESTRICT"), nullable=False)
    protocol_version_id: Mapped[int | None] = mapped_column(ForeignKey("protocol_versions.id", ondelete="RESTRICT"))
    protocol_code: Mapped[str | None] = mapped_column(String(100))
    protocol_version: Mapped[str | None] = mapped_column(String(40))
    protocol_hash: Mapped[str | None] = mapped_column(String(64))
    connection_profile_id: Mapped[int | None] = mapped_column(ForeignKey("connection_profiles.id", ondelete="RESTRICT"))
    connection_group_id: Mapped[int | None] = mapped_column(ForeignKey("connection_groups.id", ondelete="RESTRICT"))
    device_address: Mapped[str | None] = mapped_column(String(100))
    poll_priority: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    configuration_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="ASSIGNED", nullable=False)
    assigned_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("unified_users.id", ondelete="SET NULL"))
    assigned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    active_version: Mapped[str | None] = mapped_column(String(40))
    sync_status: Mapped[str] = mapped_column(String(30), default="PENDING", nullable=False)
    last_sync_error: Mapped[str | None] = mapped_column(Text)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    __table_args__ = (
        UniqueConstraint("device_id", "protocol_profile_id", name="uq_device_protocol"),
        UniqueConstraint("edge_device_id", "protocol_profile_id", name="uq_edge_device_protocol"),
    )


class UnifiedUser(TimestampMixin, Base):
    __tablename__ = "unified_users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int | None] = mapped_column(ForeignKey("companies.id", ondelete="RESTRICT"))
    station_scope_mode: Mapped[str] = mapped_column(String(32), default="ALL_COMPANY_STATIONS", nullable=False)
    username: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(40), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    first_name: Mapped[str | None] = mapped_column(String(100))
    last_name: Mapped[str | None] = mapped_column(String(100))
    email: Mapped[str | None] = mapped_column(String(255), unique=True)
    phone: Mapped[str | None] = mapped_column(String(40))
    avatar_url: Mapped[str | None] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(30), default="active", nullable=False)
    language: Mapped[str] = mapped_column(String(12), default="ar", nullable=False)
    timezone: Mapped[str] = mapped_column(String(80), default="Asia/Riyadh", nullable=False)
    country: Mapped[str | None] = mapped_column(String(100))
    city: Mapped[str | None] = mapped_column(String(100))
    role_id: Mapped[int | None] = mapped_column(ForeignKey("iam_roles.id", ondelete="SET NULL"))
    login_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_login_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_login_ip: Mapped[str | None] = mapped_column(String(80))
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    welcome_completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    voice_welcome_played: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    mfa_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    mfa_secret_ciphertext: Mapped[str | None] = mapped_column(Text)
    must_change_password: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    password_changed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class UserStation(Base):
    __tablename__ = "user_stations"
    user_id: Mapped[int] = mapped_column(ForeignKey("unified_users.id", ondelete="CASCADE"), primary_key=True)
    station_id: Mapped[int] = mapped_column(ForeignKey("stations.id", ondelete="CASCADE"), primary_key=True)


class CompanyAttachment(Base):
    __tablename__ = "company_attachments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    attachment_type: Mapped[str] = mapped_column(String(40), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(500), unique=True, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(120), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    checksum_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    uploaded_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("unified_users.id", ondelete="SET NULL"))
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    __table_args__ = (
        Index("ix_company_attachments_company_type", "company_id", "attachment_type"),
    )


class CompanyAuditEvent(Base):
    __tablename__ = "company_audit_events"
    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    company_id: Mapped[int | None] = mapped_column(ForeignKey("companies.id", ondelete="RESTRICT"))
    actor_user_id: Mapped[int | None] = mapped_column(ForeignKey("unified_users.id", ondelete="SET NULL"))
    action: Mapped[str] = mapped_column(String(80), nullable=False)
    entity_type: Mapped[str | None] = mapped_column(String(80))
    entity_id: Mapped[str | None] = mapped_column(String(120))
    details_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    __table_args__ = (
        Index("ix_company_audit_company_created", "company_id", "created_at"),
    )


class IdentityRole(TimestampMixin, Base):
    __tablename__ = "iam_roles"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    color: Mapped[str] = mapped_column(String(20), default="#5b8def", nullable=False)
    icon: Mapped[str] = mapped_column(String(60), default="shield", nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    system_role: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    immutable: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class IdentityPermission(TimestampMixin, Base):
    __tablename__ = "iam_permissions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    module: Mapped[str] = mapped_column(String(80), nullable=False)
    action: Mapped[str] = mapped_column(String(40), nullable=False)
    code: Mapped[str] = mapped_column(String(160), unique=True, nullable=False)
    name_ar: Mapped[str] = mapped_column(String(180), nullable=False)
    name_en: Mapped[str] = mapped_column(String(180), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    access_level: Mapped[str] = mapped_column(String(30), default="tenant", nullable=False)
    system_permission: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class RolePermission(Base):
    __tablename__ = "iam_role_permissions"
    role_id: Mapped[int] = mapped_column(ForeignKey("iam_roles.id", ondelete="CASCADE"), primary_key=True)
    permission_id: Mapped[int] = mapped_column(ForeignKey("iam_permissions.id", ondelete="CASCADE"), primary_key=True)


class UserPermission(TimestampMixin, Base):
    __tablename__ = "iam_user_permissions"
    user_id: Mapped[int] = mapped_column(ForeignKey("unified_users.id", ondelete="CASCADE"), primary_key=True)
    permission_id: Mapped[int] = mapped_column(ForeignKey("iam_permissions.id", ondelete="CASCADE"), primary_key=True)
    granted: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    granted_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("unified_users.id", ondelete="SET NULL"))


class IdentitySession(TimestampMixin, Base):
    __tablename__ = "iam_sessions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("unified_users.id", ondelete="CASCADE"), nullable=False)
    ip_address: Mapped[str | None] = mapped_column(String(80))
    user_agent: Mapped[str | None] = mapped_column(String(500))
    device: Mapped[str | None] = mapped_column(String(120))
    browser: Mapped[str | None] = mapped_column(String(120))
    operating_system: Mapped[str | None] = mapped_column(String(120))
    country: Mapped[str | None] = mapped_column(String(100))
    city: Mapped[str | None] = mapped_column(String(100))
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class LoginEvent(Base):
    __tablename__ = "iam_login_events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("unified_users.id", ondelete="SET NULL"))
    username: Mapped[str] = mapped_column(String(120), nullable=False)
    success: Mapped[bool] = mapped_column(Boolean, nullable=False)
    failure_reason: Mapped[str | None] = mapped_column(String(100))
    ip_address: Mapped[str | None] = mapped_column(String(80))
    user_agent: Mapped[str | None] = mapped_column(String(500))
    device: Mapped[str | None] = mapped_column(String(120))
    browser: Mapped[str | None] = mapped_column(String(120))
    operating_system: Mapped[str | None] = mapped_column(String(120))
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class DemoPolicy(TimestampMixin, Base):
    __tablename__ = "iam_demo_policies"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("unified_users.id", ondelete="CASCADE"), unique=True, nullable=False)
    starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    max_logins: Mapped[int | None] = mapped_column(Integer)
    login_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    session_minutes: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    idle_minutes: Mapped[int] = mapped_column(Integer, default=15, nullable=False)
    allow_print: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    allow_export: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    allow_download: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    allow_copy: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    allow_screenshot_ui: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    show_watermark: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class WelcomeProgress(TimestampMixin, Base):
    __tablename__ = "iam_welcome_progress"
    user_id: Mapped[int] = mapped_column(ForeignKey("unified_users.id", ondelete="CASCADE"), primary_key=True)
    completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    skipped: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    voice_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    voice_played_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_step: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class IdentitySecurityPolicy(TimestampMixin, Base):
    __tablename__ = "iam_security_policies"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int | None] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), unique=True)
    password_min_length: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    require_uppercase: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    require_lowercase: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    require_number: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    require_symbol: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    password_max_age_days: Mapped[int | None] = mapped_column(Integer, default=90)
    failed_attempt_limit: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    lock_minutes: Mapped[int] = mapped_column(Integer, default=15, nullable=False)
    max_active_sessions: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    require_mfa: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    ip_allowlist: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    device_restriction_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class TrustedIdentityDevice(TimestampMixin, Base):
    __tablename__ = "iam_trusted_devices"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("unified_users.id", ondelete="CASCADE"), nullable=False)
    fingerprint_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    name: Mapped[str | None] = mapped_column(String(160))
    trusted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = (UniqueConstraint("user_id", "fingerprint_hash", name="uq_iam_trusted_device"),)


class ApiKey(TimestampMixin, Base):
    __tablename__ = "api_keys"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    key_prefix: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    key_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    scopes: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    all_stations: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    ip_allowlist: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    rate_limit_per_minute: Mapped[int | None] = mapped_column(Integer)
    rate_limit_per_hour: Mapped[int | None] = mapped_column(Integer)
    rate_limit_per_day: Mapped[int | None] = mapped_column(Integer)
    created_by: Mapped[str | None] = mapped_column(String(120))
    request_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_ip: Mapped[str | None] = mapped_column(String(80))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ApiKeyStation(Base):
    __tablename__ = "api_key_stations"
    api_key_id: Mapped[int] = mapped_column(ForeignKey("api_keys.id", ondelete="CASCADE"), primary_key=True)
    station_id: Mapped[int] = mapped_column(ForeignKey("stations.id", ondelete="CASCADE"), primary_key=True)


class ApiRequestLog(Base):
    __tablename__ = "api_request_logs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    api_key_id: Mapped[int | None] = mapped_column(ForeignKey("api_keys.id", ondelete="SET NULL"))
    station_id: Mapped[int | None] = mapped_column(ForeignKey("stations.id", ondelete="SET NULL"))
    method: Mapped[str] = mapped_column(String(10), nullable=False)
    path: Mapped[str] = mapped_column(String(500), nullable=False)
    status_code: Mapped[int] = mapped_column(Integer, nullable=False)
    ip_address: Mapped[str | None] = mapped_column(String(80))
    duration_ms: Mapped[int | None] = mapped_column(Integer)
    scope: Mapped[str | None] = mapped_column(String(120))
    user_agent: Mapped[str | None] = mapped_column(String(300))
    request_size: Mapped[int | None] = mapped_column(Integer)
    response_size: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class Webhook(TimestampMixin, Base):
    __tablename__ = "webhooks"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    station_id: Mapped[int | None] = mapped_column(ForeignKey("stations.id", ondelete="CASCADE"))
    target_url: Mapped[str] = mapped_column(String(500), nullable=False)
    events: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    shadow_only: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_preview_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("unified_users.id", ondelete="SET NULL"))
    station_id: Mapped[int | None] = mapped_column(ForeignKey("stations.id", ondelete="SET NULL"))
    action: Mapped[str] = mapped_column(String(120), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(80), nullable=False)
    entity_id: Mapped[str | None] = mapped_column(String(120))
    before_json: Mapped[dict | None] = mapped_column(JSON)
    after_json: Mapped[dict | None] = mapped_column(JSON)
    ip_address: Mapped[str | None] = mapped_column(String(80))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class Alarm(TimestampMixin, Base):
    __tablename__ = "alarms"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    station_id: Mapped[int] = mapped_column(ForeignKey("stations.id", ondelete="RESTRICT"), nullable=False)
    device_id: Mapped[int | None] = mapped_column(ForeignKey("devices.id", ondelete="SET NULL"))
    code: Mapped[str] = mapped_column(String(80), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="open", nullable=False)


class Pump(TimestampMixin, Base):
    __tablename__ = "pumps"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    station_id: Mapped[int] = mapped_column(ForeignKey("stations.id", ondelete="RESTRICT"), nullable=False)
    pump_id: Mapped[str] = mapped_column(String(100), nullable=False)
    pump_number: Mapped[int] = mapped_column(Integer, nullable=False)
    name_ar: Mapped[str] = mapped_column(String(160), nullable=False)
    name_en: Mapped[str | None] = mapped_column(String(160))
    vendor: Mapped[str | None] = mapped_column(String(100))
    model: Mapped[str | None] = mapped_column(String(100))
    device_address: Mapped[str | None] = mapped_column(String(100))
    protocol_profile_id: Mapped[int | None] = mapped_column(ForeignKey("protocol_profiles.id", ondelete="RESTRICT"))
    connection_profile_id: Mapped[int | None] = mapped_column(ForeignKey("connection_profiles.id", ondelete="RESTRICT"))
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    color: Mapped[str] = mapped_column(String(20), default="#138bb8", nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="unknown", nullable=False)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = (UniqueConstraint("station_id", "pump_id", name="uq_pump_station_pump_id"), UniqueConstraint("id", "station_id", name="uq_pump_id_station"), Index("ix_pumps_station_order", "station_id", "display_order"))


class Tank(TimestampMixin, Base):
    __tablename__ = "tanks"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    station_id: Mapped[int] = mapped_column(ForeignKey("stations.id", ondelete="RESTRICT"), nullable=False)
    tank_id: Mapped[str] = mapped_column(String(100), nullable=False)
    tank_number: Mapped[int] = mapped_column(Integer, nullable=False)
    name_ar: Mapped[str] = mapped_column(String(160), nullable=False)
    name_en: Mapped[str | None] = mapped_column(String(160))
    fuel_type: Mapped[str] = mapped_column(String(80), nullable=False)
    fuel_code: Mapped[str] = mapped_column(String(40), nullable=False)
    fuel_color: Mapped[str] = mapped_column(String(20), nullable=False)
    capacity_liters: Mapped[float] = mapped_column(Numeric(14, 3), nullable=False)
    max_level_mm: Mapped[float] = mapped_column(Numeric(12, 3), nullable=False)
    shape: Mapped[str] = mapped_column(String(40), nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="unknown", nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    cloud_bus_device_id: Mapped[int | None] = mapped_column(ForeignKey("cloud_bus_devices.id", ondelete="SET NULL"), unique=True)
    calibration_profile_id: Mapped[int | None] = mapped_column(Integer)
    low_level_threshold: Mapped[float | None] = mapped_column(Numeric(12, 3))
    critical_low_level: Mapped[float | None] = mapped_column(Numeric(12, 3))
    high_water_threshold: Mapped[float | None] = mapped_column(Numeric(12, 3))
    temperature_warning: Mapped[float | None] = mapped_column(Numeric(8, 3))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = (
        UniqueConstraint("station_id", "tank_id", name="uq_tank_station_tank_id"),
        UniqueConstraint("tank_id", name="uq_tank_platform_code"),
        UniqueConstraint("station_id", "tank_number", name="uq_tank_station_number"),
        UniqueConstraint("id", "station_id", name="uq_tank_id_station"),
        Index("ix_tanks_station_order", "station_id", "display_order"),
    )


class Nozzle(TimestampMixin, Base):
    __tablename__ = "nozzles"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    station_id: Mapped[int] = mapped_column(ForeignKey("stations.id", ondelete="RESTRICT"), nullable=False)
    pump_id: Mapped[int] = mapped_column(Integer, nullable=False)
    nozzle_id: Mapped[str] = mapped_column(String(100), nullable=False)
    nozzle_number: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    fuel_type: Mapped[str] = mapped_column(String(80), nullable=False)
    fuel_code: Mapped[str] = mapped_column(String(40), nullable=False)
    fuel_color: Mapped[str] = mapped_column(String(20), nullable=False)
    tank_id: Mapped[int | None] = mapped_column(Integer)
    unit_price: Mapped[float | None] = mapped_column(Numeric(12, 3))
    totalizer: Mapped[float | None] = mapped_column(Numeric(18, 3))
    status: Mapped[str] = mapped_column(String(30), default="unknown", nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = (
        ForeignKeyConstraint(["pump_id", "station_id"], ["pumps.id", "pumps.station_id"], ondelete="RESTRICT", name="fk_nozzle_pump_same_station"),
        ForeignKeyConstraint(["tank_id", "station_id"], ["tanks.id", "tanks.station_id"], ondelete="RESTRICT", name="fk_nozzle_tank_same_station"),
        UniqueConstraint("pump_id", "nozzle_id", name="uq_nozzle_pump_nozzle_id"),
        UniqueConstraint("pump_id", "nozzle_number", name="uq_nozzle_pump_number"),
    )


class FuelSupplyLine(TimestampMixin, Base):
    __tablename__ = "fuel_supply_lines"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    uuid: Mapped[str] = mapped_column(String(36), nullable=False, unique=True)
    code: Mapped[str] = mapped_column(String(40), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False)
    station_id: Mapped[int] = mapped_column(ForeignKey("stations.id", ondelete="RESTRICT"), nullable=False)
    tank_id: Mapped[int] = mapped_column(ForeignKey("tanks.id", ondelete="RESTRICT"), nullable=False)
    fuel_code: Mapped[str] = mapped_column(String(40), nullable=False)
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="WAITING_FOR_PUMP_MAPPING")
    effective_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    effective_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_by: Mapped[str | None] = mapped_column(String(120))
    __table_args__ = (
        Index("ix_fuel_supply_lines_station_status", "station_id", "status"),
        Index("ix_fuel_supply_lines_tank_effective", "tank_id", "effective_from", "effective_to"),
    )


class NozzleFuelLineMapping(TimestampMixin, Base):
    __tablename__ = "nozzle_fuel_line_mappings"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pump_id: Mapped[int] = mapped_column(ForeignKey("pumps.id", ondelete="RESTRICT"), nullable=False)
    nozzle_id: Mapped[int] = mapped_column(ForeignKey("nozzles.id", ondelete="RESTRICT"), nullable=False)
    fuel_line_id: Mapped[int] = mapped_column(ForeignKey("fuel_supply_lines.id", ondelete="RESTRICT"), nullable=False)
    tank_id: Mapped[int] = mapped_column(ForeignKey("tanks.id", ondelete="RESTRICT"), nullable=False)
    effective_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    effective_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="ACTIVE")
    created_by: Mapped[str | None] = mapped_column(String(120))
    __table_args__ = (
        Index("ix_nozzle_line_mapping_nozzle_effective", "nozzle_id", "effective_from", "effective_to"),
        Index("ix_nozzle_line_mapping_tank_effective", "tank_id", "effective_from", "effective_to"),
    )


class Probe(TimestampMixin, Base):
    __tablename__ = "probes"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    station_id: Mapped[int] = mapped_column(ForeignKey("stations.id", ondelete="RESTRICT"), nullable=False)
    tank_id: Mapped[int] = mapped_column(Integer, nullable=False)
    probe_id: Mapped[str] = mapped_column(String(100), nullable=False)
    serial: Mapped[str] = mapped_column(String(100), nullable=False)
    vendor: Mapped[str | None] = mapped_column(String(100))
    model: Mapped[str | None] = mapped_column(String(160))
    probe_type: Mapped[str | None] = mapped_column(String(100))
    cloud_bus_device_id: Mapped[int | None] = mapped_column(ForeignKey("cloud_bus_devices.id", ondelete="SET NULL"), unique=True)
    protocol_profile_id: Mapped[int | None] = mapped_column(ForeignKey("protocol_profiles.id", ondelete="RESTRICT"))
    connection_profile_id: Mapped[int | None] = mapped_column(ForeignKey("connection_profiles.id", ondelete="RESTRICT"))
    enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="unknown", nullable=False)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error: Mapped[str | None] = mapped_column(Text)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = (ForeignKeyConstraint(["tank_id", "station_id"], ["tanks.id", "tanks.station_id"], ondelete="RESTRICT", name="fk_probe_tank_same_station"), UniqueConstraint("station_id", "probe_id", name="uq_probe_station_probe_id"), UniqueConstraint("station_id", "serial", name="uq_probe_station_serial"))


class Priceboard(TimestampMixin, Base):
    __tablename__ = "priceboards"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    station_id: Mapped[int] = mapped_column(ForeignKey("stations.id", ondelete="RESTRICT"), nullable=False)
    priceboard_id: Mapped[str] = mapped_column(String(100), nullable=False)
    name_ar: Mapped[str] = mapped_column(String(160), nullable=False)
    name_en: Mapped[str | None] = mapped_column(String(160))
    vendor: Mapped[str | None] = mapped_column(String(100))
    model: Mapped[str | None] = mapped_column(String(100))
    protocol_profile_id: Mapped[int | None] = mapped_column(ForeignKey("protocol_profiles.id", ondelete="RESTRICT"))
    connection_profile_id: Mapped[int | None] = mapped_column(ForeignKey("connection_profiles.id", ondelete="RESTRICT"))
    screen_rows: Mapped[int] = mapped_column(Integer, nullable=False)
    screen_mapping_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="unknown", nullable=False)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = (UniqueConstraint("station_id", "priceboard_id", name="uq_priceboard_station_id"),)


class PriceboardOperation(Base):
    __tablename__ = "priceboard_operations"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    operation_id: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    idempotency_key: Mapped[str] = mapped_column(String(190), nullable=False, unique=True)
    station_id: Mapped[int] = mapped_column(ForeignKey("stations.id", ondelete="RESTRICT"), nullable=False)
    priceboard_id: Mapped[int] = mapped_column(ForeignKey("priceboards.id", ondelete="RESTRICT"), nullable=False)
    operation_type: Mapped[str] = mapped_column(String(30), nullable=False)
    source: Mapped[str] = mapped_column(String(40), nullable=False, default="operations_center")
    requested_by: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="queued")
    requested_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    result_json: Mapped[dict | None] = mapped_column(JSON)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_code: Mapped[str | None] = mapped_column(String(80))
    error_message: Mapped[str | None] = mapped_column(Text)
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = (
        Index("ix_priceboard_operations_board_requested", "priceboard_id", "requested_at"),
        Index("ix_priceboard_operations_station_status", "station_id", "status"),
    )


class PriceboardOperationItem(Base):
    __tablename__ = "priceboard_operation_items"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    operation_id: Mapped[int] = mapped_column(ForeignKey("priceboard_operations.id", ondelete="CASCADE"), nullable=False)
    row_number: Mapped[int | None] = mapped_column(Integer)
    fuel_code: Mapped[str | None] = mapped_column(String(40))
    old_value: Mapped[str | None] = mapped_column(String(40))
    new_value: Mapped[str | None] = mapped_column(String(40))
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="queued")
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    ack_hex: Mapped[str | None] = mapped_column(Text)
    error_message: Mapped[str | None] = mapped_column(Text)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class FuelPrice(TimestampMixin, Base):
    __tablename__ = "fuel_prices"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    station_id: Mapped[int] = mapped_column(ForeignKey("stations.id", ondelete="RESTRICT"), nullable=False)
    fuel_code: Mapped[str] = mapped_column(String(40), nullable=False)
    fuel_name_ar: Mapped[str] = mapped_column(String(120), nullable=False)
    fuel_name_en: Mapped[str] = mapped_column(String(120), nullable=False)
    price: Mapped[float] = mapped_column(Numeric(12, 3), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="SAR", nullable=False)
    effective_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    __table_args__ = (UniqueConstraint("station_id", "fuel_code", "effective_at", name="uq_fuel_price_effective"), Index("ix_fuel_prices_station_active", "station_id", "active"))


class PriceChangeLog(Base):
    __tablename__ = "price_change_logs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    station_id: Mapped[int] = mapped_column(ForeignKey("stations.id", ondelete="RESTRICT"), nullable=False)
    fuel_code: Mapped[str] = mapped_column(String(40), nullable=False)
    old_price: Mapped[float | None] = mapped_column(Numeric(12, 3))
    new_price: Mapped[float] = mapped_column(Numeric(12, 3), nullable=False)
    changed_by: Mapped[str] = mapped_column(String(120), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class ShiftSession(TimestampMixin, Base):
    __tablename__ = "shift_sessions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int | None] = mapped_column(ForeignKey("companies.id", ondelete="RESTRICT"))
    station_id: Mapped[int] = mapped_column(ForeignKey("stations.id", ondelete="RESTRICT"), nullable=False)
    shift_slot: Mapped[str] = mapped_column(String(20), nullable=False)
    shift_label: Mapped[str] = mapped_column(String(120), nullable=False)
    mode: Mapped[str] = mapped_column(String(20), nullable=False, default="single")
    planned_start_time: Mapped[str] = mapped_column(String(10), nullable=False)
    planned_end_time: Mapped[str] = mapped_column(String(10), nullable=False)
    actual_started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    actual_closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    opened_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("unified_users.id", ondelete="SET NULL"))
    closed_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("unified_users.id", ondelete="SET NULL"))
    opened_by: Mapped[str | None] = mapped_column(String(120))
    closed_by: Mapped[str | None] = mapped_column(String(120))
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="active")
    sales_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sales_liters: Mapped[float] = mapped_column(Numeric(14, 3), nullable=False, default=0)
    sales_amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    pump_changes_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    nozzle_changes_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    price_changes_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    notes: Mapped[str | None] = mapped_column(Text)
    summary_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    metadata_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    __table_args__ = (
        Index("ix_shift_sessions_station_started", "station_id", "actual_started_at"),
        Index("ix_shift_sessions_station_status", "station_id", "status"),
    )


class SaleTransaction(TimestampMixin, Base):
    """Immutable-by-default record of a single pump filling operation."""
    __tablename__ = "sale_transactions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int | None] = mapped_column(ForeignKey("companies.id", ondelete="RESTRICT"))
    station_id: Mapped[int] = mapped_column(ForeignKey("stations.id", ondelete="RESTRICT"), nullable=False)
    shift_id: Mapped[int | None] = mapped_column(ForeignKey("shift_sessions.id", ondelete="RESTRICT"))
    employee_id: Mapped[int | None] = mapped_column(ForeignKey("unified_users.id", ondelete="SET NULL"))
    customer_id: Mapped[int | None] = mapped_column(ForeignKey("customers.id", ondelete="SET NULL"))
    fueling_session_id: Mapped[int | None] = mapped_column(ForeignKey("fueling_sessions.id", ondelete="SET NULL"), unique=True)
    transaction_key: Mapped[str] = mapped_column(String(160), nullable=False)
    pump_id: Mapped[int | None] = mapped_column(ForeignKey("pumps.id", ondelete="SET NULL"))
    nozzle_id: Mapped[int | None] = mapped_column(ForeignKey("nozzles.id", ondelete="SET NULL"))
    pump_number: Mapped[int] = mapped_column(Integer, nullable=False)
    nozzle_number: Mapped[int] = mapped_column(Integer, nullable=False)
    fuel_code: Mapped[str] = mapped_column(String(40), nullable=False)
    fuel_name_ar: Mapped[str] = mapped_column(String(120), nullable=False)
    liters: Mapped[float] = mapped_column(Numeric(14, 3), nullable=False, default=0)
    unit_price: Mapped[float] = mapped_column(Numeric(12, 3), nullable=False, default=0)
    amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="completed")
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    source: Mapped[str] = mapped_column(String(40), nullable=False, default="device_agent")
    payment_method: Mapped[str | None] = mapped_column(String(40))
    raw_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    __table_args__ = (
        UniqueConstraint("station_id", "transaction_key", name="uq_sale_station_transaction_key"),
        Index("ix_sales_station_started", "station_id", "started_at"),
        Index("ix_sales_station_shift", "station_id", "shift_id", "started_at"),
        Index("ix_sales_station_fuel", "station_id", "fuel_code", "started_at"),
        Index("ix_sales_station_pump_nozzle", "station_id", "pump_number", "nozzle_number", "started_at"),
    )


class Customer(TimestampMixin, Base):
    __tablename__ = "customers"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False)
    customer_type: Mapped[str] = mapped_column(String(20), nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    mobile: Mapped[str] = mapped_column(String(40), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255))
    identity_number: Mapped[str] = mapped_column(String(80), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="active")
    password_hash: Mapped[str | None] = mapped_column(String(255))
    public_id: Mapped[str | None] = mapped_column(String(36), unique=True)
    email_normalized: Mapped[str | None] = mapped_column(String(255), unique=True)
    email_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    identity_role: Mapped[str] = mapped_column(String(24), nullable=False, default="CUSTOMER")
    failed_login_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    avatar_url: Mapped[str | None] = mapped_column(String(500))
    mobile_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    __table_args__ = (UniqueConstraint("company_id", "identity_number", name="uq_customer_company_identity"),)


class CustomerWallet(TimestampMixin, Base):
    __tablename__ = "customer_wallets"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False)
    balance: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    reserved_balance: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="SAR")
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    __table_args__ = (UniqueConstraint("customer_id", name="uq_customer_wallet"),)


class WalletTransaction(Base):
    __tablename__ = "wallet_transactions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False)
    wallet_id: Mapped[int] = mapped_column(ForeignKey("customer_wallets.id", ondelete="RESTRICT"), nullable=False)
    transaction_type: Mapped[str] = mapped_column(String(24), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    balance_before: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    balance_after: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    reference: Mapped[str] = mapped_column(String(160), nullable=False)
    executed_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("unified_users.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    metadata_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    idempotency_key: Mapped[str | None] = mapped_column(String(190))
    __table_args__ = (UniqueConstraint("wallet_id", "reference", "transaction_type", name="uq_wallet_reference_type"),)


class RFIDSubscription(TimestampMixin, Base):
    __tablename__ = "rfid_subscriptions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False)
    subscription_type: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="active")
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    daily_limit: Mapped[float | None] = mapped_column(Numeric(14, 2))
    monthly_limit: Mapped[float | None] = mapped_column(Numeric(14, 2))
    per_transaction_limit: Mapped[float | None] = mapped_column(Numeric(14, 2))
    daily_transactions_limit: Mapped[int | None] = mapped_column(Integer)
    allowed_times_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)


class RFIDCard(TimestampMixin, Base):
    __tablename__ = "rfid_cards"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False)
    subscription_id: Mapped[int] = mapped_column(ForeignKey("rfid_subscriptions.id", ondelete="RESTRICT"), nullable=False)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False)
    uid: Mapped[str] = mapped_column(String(160), nullable=False, unique=True)
    linked_type: Mapped[str] = mapped_column(String(20), nullable=False, default="customer")
    linked_id: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="active")
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    issued_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("unified_users.id", ondelete="SET NULL"))
    replaced_card_id: Mapped[int | None] = mapped_column(ForeignKey("rfid_cards.id", ondelete="SET NULL"))


class Vehicle(TimestampMixin, Base):
    __tablename__ = "customer_vehicles"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    plate_number: Mapped[str] = mapped_column(String(80), nullable=False)
    vehicle_type: Mapped[str | None] = mapped_column(String(80))
    fuel_code: Mapped[str] = mapped_column(String(40), nullable=False)
    registration_number: Mapped[str | None] = mapped_column(String(120))
    nickname: Mapped[str | None] = mapped_column(String(120))
    model: Mapped[str | None] = mapped_column(String(120))
    year: Mapped[int | None] = mapped_column(Integer)
    image_url: Mapped[str | None] = mapped_column(String(500))
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = (UniqueConstraint("company_id", "plate_number", name="uq_vehicle_company_plate"),)


class Driver(TimestampMixin, Base):
    __tablename__ = "customer_drivers"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    mobile: Mapped[str] = mapped_column(String(40), nullable=False)


class CustomerStationAccess(Base):
    __tablename__ = "customer_station_access"
    subscription_id: Mapped[int] = mapped_column(ForeignKey("rfid_subscriptions.id", ondelete="CASCADE"), primary_key=True)
    station_id: Mapped[int] = mapped_column(ForeignKey("stations.id", ondelete="RESTRICT"), primary_key=True)


class CustomerFuelAccess(Base):
    __tablename__ = "customer_fuel_access"
    subscription_id: Mapped[int] = mapped_column(ForeignKey("rfid_subscriptions.id", ondelete="CASCADE"), primary_key=True)
    fuel_code: Mapped[str] = mapped_column(String(40), primary_key=True)


class CustomerDeviceSession(TimestampMixin, Base):
    __tablename__ = "customer_device_sessions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    token_family_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    device_id: Mapped[str] = mapped_column(String(160), nullable=False)
    refresh_token_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    ip_address: Mapped[str | None] = mapped_column(String(80))
    user_agent: Mapped[str | None] = mapped_column(String(500))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoke_reason: Mapped[str | None] = mapped_column(String(80))
    replaced_by_session_id: Mapped[str | None] = mapped_column(String(64))
    __table_args__ = (Index("ix_customer_session_customer_device", "customer_id", "device_id"),)


class WalletHold(TimestampMixin, Base):
    __tablename__ = "wallet_holds"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    public_id: Mapped[str] = mapped_column(String(36), nullable=False, unique=True)
    wallet_id: Mapped[int] = mapped_column(ForeignKey("customer_wallets.id", ondelete="RESTRICT"), nullable=False)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(190), nullable=False, unique=True)
    amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    captured_amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="SAR")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="HELD")
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    released_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class CustomerPaymentIntent(TimestampMixin, Base):
    __tablename__ = "customer_payment_intents"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    public_id: Mapped[str] = mapped_column(String(36), nullable=False, unique=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False)
    wallet_id: Mapped[int] = mapped_column(ForeignKey("customer_wallets.id", ondelete="RESTRICT"), nullable=False)
    gateway_id: Mapped[int] = mapped_column(ForeignKey("payment_gateways.id", ondelete="RESTRICT"), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(190), nullable=False, unique=True)
    provider_payment_intent_id: Mapped[str] = mapped_column(String(190), nullable=False, unique=True)
    amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="SAR")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pendingPayment")
    client_secret_ciphertext: Mapped[str | None] = mapped_column(Text)
    failure_code: Mapped[str | None] = mapped_column(String(100))
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class CustomerQrToken(TimestampMixin, Base):
    __tablename__ = "customer_qr_tokens"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    public_id: Mapped[str | None] = mapped_column(String(36), unique=True)
    token_ciphertext: Mapped[str | None] = mapped_column(Text)
    station_id: Mapped[int] = mapped_column(ForeignKey("stations.id", ondelete="CASCADE"), nullable=False)
    pump_id: Mapped[int] = mapped_column(ForeignKey("pumps.id", ondelete="CASCADE"), nullable=False)
    nozzle_id: Mapped[int] = mapped_column(ForeignKey("nozzles.id", ondelete="CASCADE"), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    rotated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("unified_users.id", ondelete="SET NULL"))


class CustomerQrResolution(TimestampMixin, Base):
    __tablename__ = "customer_qr_resolutions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    public_id: Mapped[str] = mapped_column(String(36), nullable=False, unique=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    qr_token_id: Mapped[int] = mapped_column(ForeignKey("customer_qr_tokens.id", ondelete="RESTRICT"), nullable=False)
    station_id: Mapped[int] = mapped_column(ForeignKey("stations.id", ondelete="RESTRICT"), nullable=False)
    pump_id: Mapped[int] = mapped_column(ForeignKey("pumps.id", ondelete="RESTRICT"), nullable=False)
    nozzle_id: Mapped[int] = mapped_column(ForeignKey("nozzles.id", ondelete="RESTRICT"), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class CustomerRealtimeEvent(Base):
    __tablename__ = "customer_realtime_events"
    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    event_type: Mapped[str] = mapped_column(String(80), nullable=False)
    entity_id: Mapped[str | None] = mapped_column(String(80))
    event_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    payload_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    __table_args__ = (Index("ix_customer_realtime_customer_id", "customer_id", "id"),)


class CustomerAuditEvent(Base):
    __tablename__ = "customer_audit_events"
    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    customer_id: Mapped[int | None] = mapped_column(ForeignKey("customers.id", ondelete="SET NULL"))
    company_id: Mapped[int | None] = mapped_column(ForeignKey("companies.id", ondelete="SET NULL"))
    station_id: Mapped[int | None] = mapped_column(ForeignKey("stations.id", ondelete="SET NULL"))
    fueling_session_id: Mapped[int | None] = mapped_column(ForeignKey("fueling_sessions.id", ondelete="SET NULL"))
    correlation_id: Mapped[str] = mapped_column(String(64), nullable=False)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_type: Mapped[str | None] = mapped_column(String(80))
    entity_id: Mapped[str | None] = mapped_column(String(80))
    ip_address: Mapped[str | None] = mapped_column(String(80))
    details_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    source: Mapped[str] = mapped_column(String(40), nullable=False, default="CUSTOMER_APP")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class FuelingSession(TimestampMixin, Base):
    __tablename__ = "fueling_sessions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False)
    station_id: Mapped[int] = mapped_column(ForeignKey("stations.id", ondelete="RESTRICT"), nullable=False)
    shift_id: Mapped[int] = mapped_column(ForeignKey("shift_sessions.id", ondelete="RESTRICT"), nullable=False)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False)
    subscription_id: Mapped[int] = mapped_column(ForeignKey("rfid_subscriptions.id", ondelete="RESTRICT"), nullable=False)
    wallet_id: Mapped[int] = mapped_column(ForeignKey("customer_wallets.id", ondelete="RESTRICT"), nullable=False)
    pump_id: Mapped[int] = mapped_column(ForeignKey("pumps.id", ondelete="RESTRICT"), nullable=False)
    nozzle_id: Mapped[int] = mapped_column(ForeignKey("nozzles.id", ondelete="RESTRICT"), nullable=False)
    edge_device_id: Mapped[int | None] = mapped_column(ForeignKey("edge_devices.id", ondelete="RESTRICT"))
    transaction_id: Mapped[int | None] = mapped_column(ForeignKey("sale_transactions.id", ondelete="SET NULL"))
    requested_amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    actual_amount: Mapped[float | None] = mapped_column(Numeric(14, 2))
    actual_liters: Mapped[float | None] = mapped_column(Numeric(14, 3))
    unit_price: Mapped[float | None] = mapped_column(Numeric(12, 3))
    fuel_code: Mapped[str | None] = mapped_column(String(40))
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="reserved")
    source: Mapped[str] = mapped_column(String(24), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    authorized_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    fueling_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    settled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    public_id: Mapped[str | None] = mapped_column(String(36), unique=True)
    idempotency_key: Mapped[str | None] = mapped_column(String(190), unique=True)
    vehicle_id: Mapped[int | None] = mapped_column(ForeignKey("customer_vehicles.id", ondelete="SET NULL"))
    hold_id: Mapped[int | None] = mapped_column(ForeignKey("wallet_holds.id", ondelete="RESTRICT"))
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="SAR")
    event_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    failure_code: Mapped[str | None] = mapped_column(String(80))
    failure_message: Mapped[str | None] = mapped_column(String(255))
    __table_args__ = (
        Index("ix_fueling_station_status", "station_id", "status"),
        Index("uq_fueling_active_customer", "customer_id", unique=True,
              postgresql_where=text("status IN ('reserved','command_pending','authorized','fueling','CREATED','AWAITING_FUNDS','FUNDS_HELD','QR_RESOLVED','AUTHORIZATION_QUEUED','EDGE_RECEIVED','PUMP_WAITING','PUMP_AUTHORIZED','READY_TO_FUEL','FUELING','STOP_REQUESTED','COMPLETED','SETTLEMENT_PENDING','REFUND_PENDING')"),
              sqlite_where=text("status IN ('reserved','command_pending','authorized','fueling','CREATED','AWAITING_FUNDS','FUNDS_HELD','QR_RESOLVED','AUTHORIZATION_QUEUED','EDGE_RECEIVED','PUMP_WAITING','PUMP_AUTHORIZED','READY_TO_FUEL','FUELING','STOP_REQUESTED','COMPLETED','SETTLEMENT_PENDING','REFUND_PENDING')")),
        Index("uq_fueling_active_nozzle", "station_id", "pump_id", "nozzle_id", unique=True,
              postgresql_where=text("status IN ('reserved','command_pending','authorized','fueling','CREATED','AWAITING_FUNDS','FUNDS_HELD','QR_RESOLVED','AUTHORIZATION_QUEUED','EDGE_RECEIVED','PUMP_WAITING','PUMP_AUTHORIZED','READY_TO_FUEL','FUELING','STOP_REQUESTED','COMPLETED','SETTLEMENT_PENDING','REFUND_PENDING')"),
              sqlite_where=text("status IN ('reserved','command_pending','authorized','fueling','CREATED','AWAITING_FUNDS','FUNDS_HELD','QR_RESOLVED','AUTHORIZATION_QUEUED','EDGE_RECEIVED','PUMP_WAITING','PUMP_AUTHORIZED','READY_TO_FUEL','FUELING','STOP_REQUESTED','COMPLETED','SETTLEMENT_PENDING','REFUND_PENDING')")),
    )


class PumpCommand(TimestampMixin, Base):
    __tablename__ = "pump_commands"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    command_id: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False)
    station_id: Mapped[int] = mapped_column(ForeignKey("stations.id", ondelete="RESTRICT"), nullable=False)
    shift_id: Mapped[int] = mapped_column(ForeignKey("shift_sessions.id", ondelete="RESTRICT"), nullable=False)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False)
    fueling_session_id: Mapped[int] = mapped_column(ForeignKey("fueling_sessions.id", ondelete="RESTRICT"), nullable=False)
    pump_id: Mapped[int] = mapped_column(ForeignKey("pumps.id", ondelete="RESTRICT"), nullable=False)
    nozzle_id: Mapped[int] = mapped_column(ForeignKey("nozzles.id", ondelete="RESTRICT"), nullable=False)
    transaction_id: Mapped[int | None] = mapped_column(ForeignKey("sale_transactions.id", ondelete="SET NULL"))
    amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="blocked")
    request_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    response_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    error_message: Mapped[str | None] = mapped_column(Text)
    __table_args__ = (UniqueConstraint("fueling_session_id", name="uq_pump_command_fueling_session"),)


class PaymentGateway(TimestampMixin, Base):
    __tablename__ = "payment_gateways"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False)
    provider: Mapped[str] = mapped_column(String(40), nullable=False)
    display_name: Mapped[str] = mapped_column(String(160), nullable=False)
    environment: Mapped[str] = mapped_column(String(20), nullable=False, default="sandbox")
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    base_url: Mapped[str | None] = mapped_column(String(500))
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="SAR")
    country: Mapped[str] = mapped_column(String(10), nullable=False, default="SA")
    timeout_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=20)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    sync_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    sync_interval_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=15)
    last_connected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error: Mapped[str | None] = mapped_column(Text)
    sync_cursor: Mapped[str | None] = mapped_column(String(500))
    definition_id: Mapped[int | None] = mapped_column(ForeignKey("payment_provider_definitions.id", ondelete="RESTRICT"))
    connection_token_hash: Mapped[str | None] = mapped_column(String(64), unique=True)
    integration_type: Mapped[str] = mapped_column(String(40), nullable=False, default="configurable_rest")
    auth_type: Mapped[str] = mapped_column(String(40), nullable=False, default="bearer")
    allowed_domains: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    configuration_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    tested_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    test_status: Mapped[str] = mapped_column(String(24), nullable=False, default="untested")
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = (
        UniqueConstraint("company_id", "provider", "display_name", name="uq_payment_gateway_company_name"),
        Index("ix_payment_gateway_company_enabled", "company_id", "enabled"),
    )


class PaymentGatewayCredential(TimestampMixin, Base):
    __tablename__ = "payment_gateway_credentials"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    gateway_id: Mapped[int] = mapped_column(ForeignKey("payment_gateways.id", ondelete="CASCADE"), nullable=False)
    encrypted_payload: Mapped[str] = mapped_column(Text, nullable=False)
    key_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    updated_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("unified_users.id", ondelete="SET NULL"))
    __table_args__ = (UniqueConstraint("gateway_id", name="uq_payment_gateway_credential"),)


class PaymentMerchantAccount(TimestampMixin, Base):
    __tablename__ = "payment_merchant_accounts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False)
    gateway_id: Mapped[int] = mapped_column(ForeignKey("payment_gateways.id", ondelete="RESTRICT"), nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    merchant_reference: Mapped[str] = mapped_column(String(160), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    __table_args__ = (UniqueConstraint("gateway_id", "merchant_reference", name="uq_payment_merchant_reference"),)


class PaymentTerminal(TimestampMixin, Base):
    __tablename__ = "payment_terminals"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False)
    merchant_account_id: Mapped[int] = mapped_column(ForeignKey("payment_merchant_accounts.id", ondelete="RESTRICT"), nullable=False)
    station_id: Mapped[int] = mapped_column(ForeignKey("stations.id", ondelete="RESTRICT"), nullable=False)
    terminal_reference: Mapped[str] = mapped_column(String(160), nullable=False)
    name: Mapped[str | None] = mapped_column(String(160))
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    __table_args__ = (UniqueConstraint("merchant_account_id", "terminal_reference", name="uq_payment_terminal_reference"),)


class PaymentStationMapping(TimestampMixin, Base):
    __tablename__ = "payment_station_mappings"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False)
    station_id: Mapped[int] = mapped_column(ForeignKey("stations.id", ondelete="CASCADE"), nullable=False)
    gateway_id: Mapped[int] = mapped_column(ForeignKey("payment_gateways.id", ondelete="CASCADE"), nullable=False)
    merchant_account_id: Mapped[int | None] = mapped_column(ForeignKey("payment_merchant_accounts.id", ondelete="SET NULL"))
    terminal_id: Mapped[int | None] = mapped_column(ForeignKey("payment_terminals.id", ondelete="SET NULL"))
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="SAR")
    __table_args__ = (UniqueConstraint("station_id", "gateway_id", "merchant_account_id", "terminal_id", name="uq_payment_station_mapping"),)


class PaymentTransaction(TimestampMixin, Base):
    __tablename__ = "payment_transactions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False)
    station_id: Mapped[int | None] = mapped_column(ForeignKey("stations.id", ondelete="RESTRICT"))
    customer_id: Mapped[int | None] = mapped_column(ForeignKey("customers.id", ondelete="SET NULL"))
    gateway_id: Mapped[int] = mapped_column(ForeignKey("payment_gateways.id", ondelete="RESTRICT"), nullable=False)
    merchant_account_id: Mapped[int | None] = mapped_column(ForeignKey("payment_merchant_accounts.id", ondelete="SET NULL"))
    terminal_id: Mapped[int | None] = mapped_column(ForeignKey("payment_terminals.id", ondelete="SET NULL"))
    fueling_session_id: Mapped[int | None] = mapped_column(ForeignKey("fueling_sessions.id", ondelete="SET NULL"))
    invoice_id: Mapped[int | None] = mapped_column(ForeignKey("payment_invoices.id", ondelete="SET NULL"))
    payment_link_id: Mapped[int | None] = mapped_column(ForeignKey("payment_links.id", ondelete="SET NULL"))
    provider: Mapped[str] = mapped_column(String(40), nullable=False)
    provider_transaction_id: Mapped[str] = mapped_column(String(190), nullable=False)
    external_reference: Mapped[str | None] = mapped_column(String(190))
    request_id: Mapped[str | None] = mapped_column(String(190))
    order_id: Mapped[str | None] = mapped_column(String(190))
    provider_invoice_id: Mapped[str | None] = mapped_column(String(190))
    authorization_code: Mapped[str | None] = mapped_column(String(120))
    merchant_reference: Mapped[str | None] = mapped_column(String(160))
    terminal_reference: Mapped[str | None] = mapped_column(String(160))
    amount: Mapped[float] = mapped_column(Numeric(16, 2), nullable=False)
    fees: Mapped[float] = mapped_column(Numeric(16, 2), nullable=False, default=0)
    tax: Mapped[float] = mapped_column(Numeric(16, 2), nullable=False, default=0)
    net_amount: Mapped[float] = mapped_column(Numeric(16, 2), nullable=False)
    refunded_amount: Mapped[float] = mapped_column(Numeric(16, 2), nullable=False, default=0)
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="SAR")
    payment_method: Mapped[str | None] = mapped_column(String(40))
    transaction_type: Mapped[str] = mapped_column(String(30), nullable=False, default="payment")
    payment_status: Mapped[str] = mapped_column(String(30), nullable=False)
    settlement_status: Mapped[str] = mapped_column(String(30), nullable=False, default="unsettled")
    refund_status: Mapped[str] = mapped_column(String(30), nullable=False, default="none")
    source: Mapped[str] = mapped_column(String(40), nullable=False, default="gateway")
    card_brand: Mapped[str | None] = mapped_column(String(40))
    card_last4: Mapped[str | None] = mapped_column(String(4))
    failure_code: Mapped[str | None] = mapped_column(String(100))
    failure_message: Mapped[str | None] = mapped_column(Text)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    raw_response_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    __table_args__ = (
        UniqueConstraint("company_id", "gateway_id", "provider_transaction_id", name="uq_payment_tenant_gateway_transaction"),
        Index("ix_payment_company_occurred", "company_id", "occurred_at"),
        Index("ix_payment_station_status_occurred", "station_id", "payment_status", "occurred_at"),
        Index("ix_payment_external_reference", "external_reference"),
    )


class PaymentTransactionEvent(Base):
    __tablename__ = "payment_transaction_events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    transaction_id: Mapped[int] = mapped_column(ForeignKey("payment_transactions.id", ondelete="CASCADE"), nullable=False)
    event_type: Mapped[str] = mapped_column(String(60), nullable=False)
    status_from: Mapped[str | None] = mapped_column(String(30))
    status_to: Mapped[str | None] = mapped_column(String(30))
    provider_event_id: Mapped[str | None] = mapped_column(String(190))
    payload_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    __table_args__ = (
        UniqueConstraint("provider_event_id", name="uq_payment_transaction_provider_event"),
        Index("ix_payment_event_transaction_created", "transaction_id", "created_at"),
    )


class PaymentRefund(TimestampMixin, Base):
    __tablename__ = "payment_refunds"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    transaction_id: Mapped[int] = mapped_column(ForeignKey("payment_transactions.id", ondelete="RESTRICT"), nullable=False)
    provider_refund_id: Mapped[str | None] = mapped_column(String(190))
    idempotency_key: Mapped[str] = mapped_column(String(190), nullable=False, unique=True)
    amount: Mapped[float] = mapped_column(Numeric(16, 2), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="pending")
    requested_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("unified_users.id", ondelete="SET NULL"))
    provider_response_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)


class PaymentSettlement(TimestampMixin, Base):
    __tablename__ = "payment_settlements"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    gateway_id: Mapped[int] = mapped_column(ForeignKey("payment_gateways.id", ondelete="RESTRICT"), nullable=False)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False)
    provider_settlement_id: Mapped[str] = mapped_column(String(190), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(16, 2), nullable=False)
    fees: Mapped[float] = mapped_column(Numeric(16, 2), nullable=False, default=0)
    tax: Mapped[float] = mapped_column(Numeric(16, 2), nullable=False, default=0)
    net_amount: Mapped[float] = mapped_column(Numeric(16, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="SAR")
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    settled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    payload_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    __table_args__ = (UniqueConstraint("gateway_id", "provider_settlement_id", name="uq_payment_gateway_settlement"),)


class PaymentWebhookEvent(Base):
    __tablename__ = "payment_webhook_events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    gateway_id: Mapped[int] = mapped_column(ForeignKey("payment_gateways.id", ondelete="CASCADE"), nullable=False)
    provider_event_id: Mapped[str] = mapped_column(String(190), nullable=False)
    signature_valid: Mapped[bool] = mapped_column(Boolean, nullable=False)
    event_type: Mapped[str | None] = mapped_column(String(80))
    payload_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="received")
    error_message: Mapped[str | None] = mapped_column(Text)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = (UniqueConstraint("gateway_id", "provider_event_id", name="uq_payment_webhook_event"),)


class PaymentSyncRun(Base):
    __tablename__ = "payment_sync_runs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    gateway_id: Mapped[int] = mapped_column(ForeignKey("payment_gateways.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="running")
    trigger: Mapped[str] = mapped_column(String(30), nullable=False)
    cursor_before: Mapped[str | None] = mapped_column(String(500))
    cursor_after: Mapped[str | None] = mapped_column(String(500))
    fetched_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    updated_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_message: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class PaymentGatewayLog(Base):
    __tablename__ = "payment_gateway_logs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    gateway_id: Mapped[int] = mapped_column(ForeignKey("payment_gateways.id", ondelete="CASCADE"), nullable=False)
    level: Mapped[str] = mapped_column(String(20), nullable=False)
    action: Mapped[str] = mapped_column(String(80), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    context_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    __table_args__ = (Index("ix_payment_gateway_log_created", "gateway_id", "created_at"),)


class PaymentProviderDefinition(TimestampMixin, Base):
    __tablename__ = "payment_provider_definitions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int | None] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"))
    provider_code: Mapped[str] = mapped_column(String(80), nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    adapter_type: Mapped[str] = mapped_column(String(40), nullable=False, default="configurable_rest")
    logo_url: Mapped[str | None] = mapped_column(String(500))
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    schema_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("unified_users.id", ondelete="SET NULL"))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = (UniqueConstraint("company_id", "provider_code", name="uq_payment_definition_company_code"),)


class PaymentProviderField(TimestampMixin, Base):
    __tablename__ = "payment_provider_fields"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    definition_id: Mapped[int] = mapped_column(ForeignKey("payment_provider_definitions.id", ondelete="CASCADE"), nullable=False)
    field_key: Mapped[str] = mapped_column(String(120), nullable=False)
    label: Mapped[str] = mapped_column(String(160), nullable=False)
    field_type: Mapped[str] = mapped_column(String(30), nullable=False)
    required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    secret: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    description: Mapped[str | None] = mapped_column(Text)
    __table_args__ = (UniqueConstraint("definition_id", "field_key", name="uq_payment_definition_field"),)


class PaymentProviderEndpoint(TimestampMixin, Base):
    __tablename__ = "payment_provider_endpoints"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    definition_id: Mapped[int] = mapped_column(ForeignKey("payment_provider_definitions.id", ondelete="CASCADE"), nullable=False)
    operation: Mapped[str] = mapped_column(String(60), nullable=False)
    method: Mapped[str] = mapped_column(String(10), nullable=False)
    path: Mapped[str] = mapped_column(String(500), nullable=False)
    configuration_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    __table_args__ = (UniqueConstraint("definition_id", "operation", name="uq_payment_definition_operation"),)


class PaymentProviderMapping(TimestampMixin, Base):
    __tablename__ = "payment_provider_mappings"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    definition_id: Mapped[int] = mapped_column(ForeignKey("payment_provider_definitions.id", ondelete="CASCADE"), nullable=False)
    mapping_type: Mapped[str] = mapped_column(String(30), nullable=False)
    operation: Mapped[str] = mapped_column(String(60), nullable=False, default="default")
    mapping_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    __table_args__ = (UniqueConstraint("definition_id", "mapping_type", "operation", name="uq_payment_definition_mapping"),)


class PaymentMethod(TimestampMixin, Base):
    __tablename__ = "payment_methods"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    configuration_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    __table_args__ = (UniqueConstraint("company_id", "code", name="uq_payment_method_company_code"),)


class PaymentProviderMethod(TimestampMixin, Base):
    __tablename__ = "payment_provider_methods"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    gateway_id: Mapped[int] = mapped_column(ForeignKey("payment_gateways.id", ondelete="CASCADE"), nullable=False)
    method_id: Mapped[int] = mapped_column(ForeignKey("payment_methods.id", ondelete="CASCADE"), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    minimum_minor: Mapped[int | None] = mapped_column(Integer)
    maximum_minor: Mapped[int | None] = mapped_column(Integer)
    supports_refund: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    supports_partial_refund: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    __table_args__ = (UniqueConstraint("gateway_id", "method_id", name="uq_payment_gateway_method"),)


class PaymentInvoice(TimestampMixin, Base):
    __tablename__ = "payment_invoices"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False)
    station_id: Mapped[int | None] = mapped_column(ForeignKey("stations.id", ondelete="RESTRICT"))
    customer_id: Mapped[int | None] = mapped_column(ForeignKey("customers.id", ondelete="SET NULL"))
    invoice_number: Mapped[str] = mapped_column(String(80), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    reason: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    subtotal_minor: Mapped[int] = mapped_column(Integer, nullable=False)
    discount_minor: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    tax_minor: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_minor: Mapped[int] = mapped_column(Integer, nullable=False)
    paid_minor: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    currency: Mapped[str] = mapped_column(String(10), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="DRAFT")
    customer_name: Mapped[str] = mapped_column(String(160), nullable=False)
    customer_phone: Mapped[str] = mapped_column(String(40), nullable=False)
    customer_email: Mapped[str | None] = mapped_column(String(255))
    issued_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    notes: Mapped[str | None] = mapped_column(Text)
    metadata_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("unified_users.id", ondelete="SET NULL"))
    __table_args__ = (UniqueConstraint("company_id", "invoice_number", name="uq_payment_invoice_company_number"),)


class PaymentInvoiceItem(TimestampMixin, Base):
    __tablename__ = "payment_invoice_items"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    invoice_id: Mapped[int] = mapped_column(ForeignKey("payment_invoices.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    quantity: Mapped[float] = mapped_column(Numeric(14, 3), nullable=False)
    unit_price_minor: Mapped[int] = mapped_column(Integer, nullable=False)
    discount_minor: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    tax_rate: Mapped[float] = mapped_column(Numeric(7, 4), nullable=False, default=0)
    tax_minor: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_minor: Mapped[int] = mapped_column(Integer, nullable=False)


class PaymentLink(TimestampMixin, Base):
    __tablename__ = "payment_links"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False)
    station_id: Mapped[int | None] = mapped_column(ForeignKey("stations.id", ondelete="RESTRICT"))
    invoice_id: Mapped[int] = mapped_column(ForeignKey("payment_invoices.id", ondelete="RESTRICT"), nullable=False)
    gateway_id: Mapped[int] = mapped_column(ForeignKey("payment_gateways.id", ondelete="RESTRICT"), nullable=False)
    link_number: Mapped[str] = mapped_column(String(80), nullable=False)
    public_token_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    provider_payment_id: Mapped[str | None] = mapped_column(String(190))
    provider_request_id: Mapped[str | None] = mapped_column(String(190))
    provider_url: Mapped[str | None] = mapped_column(Text)
    idempotency_key: Mapped[str] = mapped_column(String(190), nullable=False, unique=True)
    amount_minor: Mapped[int] = mapped_column(Integer, nullable=False)
    paid_minor: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    currency: Mapped[str] = mapped_column(String(10), nullable=False)
    payment_methods_json: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="CREATING")
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    viewed_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failure_code: Mapped[str | None] = mapped_column(String(100))
    failure_message: Mapped[str | None] = mapped_column(Text)
    created_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("unified_users.id", ondelete="SET NULL"))
    __table_args__ = (UniqueConstraint("company_id", "link_number", name="uq_payment_link_company_number"),)


class PaymentLinkDeliveryLog(Base):
    __tablename__ = "payment_link_delivery_logs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    payment_link_id: Mapped[int] = mapped_column(ForeignKey("payment_links.id", ondelete="CASCADE"), nullable=False)
    channel: Mapped[str] = mapped_column(String(30), nullable=False)
    recipient_masked: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    provider_reference: Mapped[str | None] = mapped_column(String(190))
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class PaymentReceipt(TimestampMixin, Base):
    __tablename__ = "payment_receipts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False)
    invoice_id: Mapped[int] = mapped_column(ForeignKey("payment_invoices.id", ondelete="RESTRICT"), nullable=False)
    transaction_id: Mapped[int] = mapped_column(ForeignKey("payment_transactions.id", ondelete="RESTRICT"), nullable=False)
    receipt_number: Mapped[str] = mapped_column(String(80), nullable=False)
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    __table_args__ = (UniqueConstraint("company_id", "receipt_number", name="uq_payment_receipt_company_number"),)


class EnergyReportDelivery(Base):
    __tablename__ = "energy_report_deliveries"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    station_id: Mapped[int] = mapped_column(ForeignKey("stations.id", ondelete="RESTRICT"), nullable=False)
    report_type: Mapped[str] = mapped_column(String(40), nullable=False)
    channel: Mapped[str] = mapped_column(String(20), nullable=False)
    period_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    period_to: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    filters_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="queued")
    recipient: Mapped[str | None] = mapped_column(String(500))
    response_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    error_message: Mapped[str | None] = mapped_column(Text)
    sent_by: Mapped[str | None] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = (Index("ix_energy_delivery_station_created", "station_id", "created_at"),)


class TankDelivery(TimestampMixin, Base):
    __tablename__ = "tank_deliveries"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    station_id: Mapped[int] = mapped_column(ForeignKey("stations.id", ondelete="RESTRICT"), nullable=False)
    tank_id: Mapped[int] = mapped_column(ForeignKey("tanks.id", ondelete="RESTRICT"), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    baseline_liters: Mapped[float] = mapped_column(Numeric(14, 3), nullable=False)
    peak_liters: Mapped[float] = mapped_column(Numeric(14, 3), nullable=False)
    added_liters: Mapped[float] = mapped_column(Numeric(14, 3), nullable=False, default=0)
    added_percent: Mapped[float] = mapped_column(Numeric(8, 3), nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="detecting")
    source: Mapped[str] = mapped_column(String(40), nullable=False, default="tank_level_auto")
    __table_args__ = (Index("ix_tank_deliveries_station_started", "station_id", "started_at"),)


class TankLevelState(Base):
    __tablename__ = "tank_level_states"
    tank_id: Mapped[int] = mapped_column(ForeignKey("tanks.id", ondelete="CASCADE"), primary_key=True)
    station_id: Mapped[int] = mapped_column(ForeignKey("stations.id", ondelete="RESTRICT"), nullable=False)
    stable_liters: Mapped[float] = mapped_column(Numeric(14, 3), nullable=False)
    last_liters: Mapped[float] = mapped_column(Numeric(14, 3), nullable=False)
    peak_liters: Mapped[float] = mapped_column(Numeric(14, 3), nullable=False)
    meter_inventory_liters: Mapped[float | None] = mapped_column(Numeric(14, 3))
    sales_total_liters: Mapped[float] = mapped_column(Numeric(18, 3), nullable=False, default=0)
    delivery_total_liters: Mapped[float] = mapped_column(Numeric(18, 3), nullable=False, default=0)
    sensor_variance_liters: Mapped[float] = mapped_column(Numeric(14, 3), nullable=False, default=0)
    active_delivery_id: Mapped[int | None] = mapped_column(ForeignKey("tank_deliveries.id", ondelete="SET NULL"))
    last_change_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class TankCalibrationRun(TimestampMixin, Base):
    __tablename__ = "tank_calibration_runs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    station_id: Mapped[int] = mapped_column(ForeignKey("stations.id", ondelete="RESTRICT"), nullable=False)
    tank_id: Mapped[int] = mapped_column(ForeignKey("tanks.id", ondelete="RESTRICT"), nullable=False)
    fuel_code: Mapped[str] = mapped_column(String(40), nullable=False)
    target_liters: Mapped[float] = mapped_column(Numeric(14, 3), nullable=False)
    baseline_total_liters: Mapped[float] = mapped_column(Numeric(18, 3), nullable=False)
    baseline_level_mm: Mapped[float] = mapped_column(Numeric(12, 3), nullable=False)
    latest_total_liters: Mapped[float] = mapped_column(Numeric(18, 3), nullable=False)
    latest_level_mm: Mapped[float] = mapped_column(Numeric(12, 3), nullable=False)
    actual_liters: Mapped[float] = mapped_column(Numeric(14, 3), nullable=False, default=0)
    level_drop_mm: Mapped[float] = mapped_column(Numeric(12, 3), nullable=False, default=0)
    liters_per_mm: Mapped[float | None] = mapped_column(Numeric(16, 6))
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="monitoring")
    quality_status: Mapped[str] = mapped_column(String(24), nullable=False, default="pending")
    samples_json: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    last_change_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    approved_by: Mapped[str | None] = mapped_column(String(120))
    notes: Mapped[str | None] = mapped_column(Text)
    __table_args__ = (Index("ix_calibration_tank_created", "tank_id", "created_at"),)


class TankCalibrationProfile(TimestampMixin, Base):
    __tablename__ = "tank_calibration_profiles"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    station_id: Mapped[int] = mapped_column(ForeignKey("stations.id", ondelete="RESTRICT"), nullable=False)
    tank_id: Mapped[int] = mapped_column(ForeignKey("tanks.id", ondelete="RESTRICT"), nullable=False, unique=True)
    liters_per_mm: Mapped[float] = mapped_column(Numeric(16, 6), nullable=False)
    source_run_id: Mapped[int] = mapped_column(ForeignKey("tank_calibration_runs.id", ondelete="RESTRICT"), nullable=False)
    sample_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    applied_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    applied_by: Mapped[str] = mapped_column(String(120), nullable=False)


class TankGeometry(TimestampMixin, Base):
    __tablename__ = "tank_geometries"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    station_id: Mapped[int] = mapped_column(ForeignKey("stations.id", ondelete="RESTRICT"), nullable=False)
    tank_id: Mapped[int] = mapped_column(ForeignKey("tanks.id", ondelete="RESTRICT"), nullable=False, unique=True)
    probe_serial: Mapped[str] = mapped_column(String(100), nullable=False)
    capacity_liters: Mapped[float] = mapped_column(Numeric(14, 3), nullable=False)
    height_mm: Mapped[float] = mapped_column(Numeric(12, 3), nullable=False)
    fuel_type: Mapped[str] = mapped_column(String(80), nullable=False)
    learning_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    active_version_id: Mapped[int | None] = mapped_column(Integer)
    last_learning_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class CalibrationVersion(TimestampMixin, Base):
    __tablename__ = "calibration_versions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    station_id: Mapped[int] = mapped_column(ForeignKey("stations.id", ondelete="RESTRICT"), nullable=False)
    tank_id: Mapped[int] = mapped_column(ForeignKey("tanks.id", ondelete="RESTRICT"), nullable=False)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    source: Mapped[str] = mapped_column(String(24), nullable=False, default="learned")
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="pending_approval")
    description: Mapped[str | None] = mapped_column(Text)
    confidence: Mapped[float] = mapped_column(Numeric(7, 4), nullable=False, default=0)
    accuracy: Mapped[float | None] = mapped_column(Numeric(7, 4))
    session_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    rmse_liters: Mapped[float | None] = mapped_column(Numeric(14, 4))
    mean_error_liters: Mapped[float | None] = mapped_column(Numeric(14, 4))
    max_error_liters: Mapped[float | None] = mapped_column(Numeric(14, 4))
    standard_deviation: Mapped[float | None] = mapped_column(Numeric(14, 6))
    variance: Mapped[float | None] = mapped_column(Numeric(18, 6))
    created_by: Mapped[str | None] = mapped_column(String(120))
    approved_by: Mapped[str | None] = mapped_column(String(120))
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    activated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = (UniqueConstraint("tank_id", "version_number", name="uq_calibration_version_tank_number"), Index("ix_calibration_version_tank_created", "tank_id", "created_at"))


class LearningSession(TimestampMixin, Base):
    __tablename__ = "learning_sessions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    station_id: Mapped[int] = mapped_column(ForeignKey("stations.id", ondelete="RESTRICT"), nullable=False)
    tank_id: Mapped[int] = mapped_column(ForeignKey("tanks.id", ondelete="RESTRICT"), nullable=False)
    expected_delivery_liters: Mapped[float] = mapped_column(Numeric(14, 3), nullable=False)
    delivery_source: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(64), nullable=False, default="monitoring")
    baseline_level_mm: Mapped[float | None] = mapped_column(Numeric(12, 3))
    baseline_sales_liters: Mapped[float] = mapped_column(Numeric(18, 3), nullable=False, default=0)
    delivered_liters: Mapped[float] = mapped_column(Numeric(14, 3), nullable=False, default=0)
    pump_sales_liters: Mapped[float] = mapped_column(Numeric(14, 3), nullable=False, default=0)
    net_added_liters: Mapped[float] = mapped_column(Numeric(14, 3), nullable=False, default=0)
    confidence: Mapped[float] = mapped_column(Numeric(7, 4), nullable=False, default=0)
    rejection_reason: Mapped[str | None] = mapped_column(String(160))
    raw_sample_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    stable_sample_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    filter_state_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    started_by: Mapped[str | None] = mapped_column(String(120))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = (Index("ix_learning_session_tank_started", "tank_id", "started_at"),)


class CalibrationSample(Base):
    __tablename__ = "calibration_samples"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("learning_sessions.id", ondelete="CASCADE"), nullable=False)
    tank_id: Mapped[int] = mapped_column(ForeignKey("tanks.id", ondelete="RESTRICT"), nullable=False)
    level_mm: Mapped[float] = mapped_column(Numeric(12, 3), nullable=False)
    real_liters: Mapped[float] = mapped_column(Numeric(14, 3), nullable=False)
    water_level_mm: Mapped[float | None] = mapped_column(Numeric(12, 3))
    temperature_c: Mapped[float | None] = mapped_column(Numeric(8, 3))
    pump_sales_liters: Mapped[float] = mapped_column(Numeric(14, 3), nullable=False, default=0)
    fuel_rate_lpm: Mapped[float | None] = mapped_column(Numeric(14, 4))
    fuel_velocity_mm_s: Mapped[float | None] = mapped_column(Numeric(14, 6))
    moving_average_mm: Mapped[float] = mapped_column(Numeric(12, 3), nullable=False)
    noise_level_mm: Mapped[float] = mapped_column(Numeric(12, 4), nullable=False)
    signal_stability: Mapped[float] = mapped_column(Numeric(7, 4), nullable=False)
    surface_stability: Mapped[float] = mapped_column(Numeric(7, 4), nullable=False)
    confidence: Mapped[float] = mapped_column(Numeric(7, 4), nullable=False)
    measured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    __table_args__ = (Index("ix_calibration_sample_tank_level", "tank_id", "level_mm"), Index("ix_calibration_sample_session_time", "session_id", "measured_at"))


class CalibrationObservation(TimestampMixin, Base):
    __tablename__ = "calibration_observations"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tank_id: Mapped[int] = mapped_column(ForeignKey("tanks.id", ondelete="RESTRICT"), nullable=False)
    learning_session_id: Mapped[int | None] = mapped_column(ForeignKey("learning_sessions.id", ondelete="SET NULL"))
    candidate_version_id: Mapped[int | None] = mapped_column(ForeignKey("calibration_versions.id", ondelete="SET NULL"))
    before_level_mm: Mapped[float | None] = mapped_column(Numeric(12, 3))
    after_level_mm: Mapped[float | None] = mapped_column(Numeric(12, 3))
    delta_mm: Mapped[float | None] = mapped_column(Numeric(12, 3))
    sales_liters: Mapped[float] = mapped_column(Numeric(14, 3), nullable=False, default=0)
    transaction_ids_json: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    fuel_line_ids_json: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    nozzle_ids_json: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    temperature_before: Mapped[float | None] = mapped_column(Numeric(8, 3))
    temperature_after: Mapped[float | None] = mapped_column(Numeric(8, 3))
    water_before: Mapped[float | None] = mapped_column(Numeric(12, 3))
    water_after: Mapped[float | None] = mapped_column(Numeric(12, 3))
    window_started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    window_ended_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    quality: Mapped[float] = mapped_column(Numeric(7, 4), nullable=False, default=0)
    confidence: Mapped[float] = mapped_column(Numeric(7, 4), nullable=False, default=0)
    accepted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    rejection_reason: Mapped[str | None] = mapped_column(String(80))
    evidence_type: Mapped[str] = mapped_column(String(40), nullable=False, default="SALES_WITHDRAWAL")
    observation_key: Mapped[str | None] = mapped_column(String(64), unique=True)
    __table_args__ = (
        Index("ix_calibration_observation_tank_time", "tank_id", "window_ended_at"),
        Index("ix_calibration_observation_session_accepted", "learning_session_id", "accepted"),
    )


class SaleTankAttribution(TimestampMixin, Base):
    __tablename__ = "sale_tank_attributions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sale_transaction_id: Mapped[int] = mapped_column(
        ForeignKey("sale_transactions.id", ondelete="RESTRICT"), nullable=False, unique=True
    )
    station_id: Mapped[int] = mapped_column(ForeignKey("stations.id", ondelete="RESTRICT"), nullable=False)
    transaction_id: Mapped[str] = mapped_column(String(160), nullable=False)
    pump_id: Mapped[int] = mapped_column(ForeignKey("pumps.id", ondelete="RESTRICT"), nullable=False)
    nozzle_id: Mapped[int] = mapped_column(ForeignKey("nozzles.id", ondelete="RESTRICT"), nullable=False)
    fuel_line_id: Mapped[int] = mapped_column(ForeignKey("fuel_supply_lines.id", ondelete="RESTRICT"), nullable=False)
    tank_id: Mapped[int] = mapped_column(ForeignKey("tanks.id", ondelete="RESTRICT"), nullable=False)
    liters: Mapped[float] = mapped_column(Numeric(14, 3), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ended_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="ATTRIBUTED")
    rejection_reason: Mapped[str | None] = mapped_column(String(80))
    __table_args__ = (
        UniqueConstraint("station_id", "transaction_id", name="uq_sale_attribution_station_transaction"),
        Index("ix_sale_attribution_tank_ended", "tank_id", "ended_at"),
    )


class CalibrationInternalEvent(TimestampMixin, Base):
    __tablename__ = "calibration_internal_events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_id: Mapped[str] = mapped_column(String(36), nullable=False, unique=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    tank_id: Mapped[int] = mapped_column(ForeignKey("tanks.id", ondelete="RESTRICT"), nullable=False)
    attribution_id: Mapped[int | None] = mapped_column(
        ForeignKey("sale_tank_attributions.id", ondelete="RESTRICT")
    )
    payload_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="PENDING")
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    available_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error: Mapped[str | None] = mapped_column(Text)
    __table_args__ = (Index("ix_calibration_event_pending", "status", "available_at"),)


class CalibrationPackageVersion(TimestampMixin, Base):
    __tablename__ = "calibration_package_versions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    package_id: Mapped[str] = mapped_column(String(36), nullable=False, unique=True)
    tank_id: Mapped[int] = mapped_column(ForeignKey("tanks.id", ondelete="RESTRICT"), nullable=False)
    calibration_version_id: Mapped[int] = mapped_column(
        ForeignKey("calibration_versions.id", ondelete="RESTRICT"), nullable=False
    )
    profile_version: Mapped[str] = mapped_column(String(40), nullable=False)
    table_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    definition_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    lookup_table_json: Mapped[list] = mapped_column(JSON, nullable=False)
    confidence_map_json: Mapped[list] = mapped_column(JSON, nullable=False)
    envelope_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    payload_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    signature: Mapped[str] = mapped_column(Text, nullable=False)
    signature_algorithm: Mapped[str] = mapped_column(String(40), nullable=False, default="Ed25519")
    signing_key_id: Mapped[str] = mapped_column(String(160), nullable=False)
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="ACTIVE")
    __table_args__ = (
        UniqueConstraint("tank_id", "calibration_version_id", name="uq_calibration_package_version"),
    )


class CalibrationDelivery(TimestampMixin, Base):
    __tablename__ = "calibration_deliveries"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    delivery_id: Mapped[str] = mapped_column(String(36), nullable=False, unique=True)
    package_version_id: Mapped[int] = mapped_column(
        ForeignKey("calibration_package_versions.id", ondelete="RESTRICT"), nullable=False
    )
    edge_device_id: Mapped[int] = mapped_column(
        ForeignKey("edge_devices.id", ondelete="RESTRICT"), nullable=False
    )
    tank_id: Mapped[int] = mapped_column(ForeignKey("tanks.id", ondelete="RESTRICT"), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="PENDING")
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    response_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    error_code: Mapped[str | None] = mapped_column(String(100))
    error_message: Mapped[str | None] = mapped_column(Text)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    __table_args__ = (Index("ix_calibration_delivery_edge_status", "edge_device_id", "status"),)


class CalibrationAnchor(TimestampMixin, Base):
    __tablename__ = "calibration_anchors"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tank_id: Mapped[int] = mapped_column(ForeignKey("tanks.id", ondelete="RESTRICT"), nullable=False)
    version_id: Mapped[int | None] = mapped_column(ForeignKey("calibration_versions.id", ondelete="CASCADE"))
    level_mm: Mapped[float] = mapped_column(Numeric(12, 3), nullable=False)
    volume_liters: Mapped[float] = mapped_column(Numeric(14, 3), nullable=False)
    source: Mapped[str] = mapped_column(String(32), nullable=False)
    confidence: Mapped[float] = mapped_column(Numeric(7, 4), nullable=False, default=1)
    certified_reference: Mapped[str | None] = mapped_column(String(160))
    created_by: Mapped[str | None] = mapped_column(String(120))
    __table_args__ = (Index("ix_calibration_anchor_tank_level", "tank_id", "level_mm"),)


class ConfidenceMap(Base):
    __tablename__ = "confidence_maps"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    version_id: Mapped[int] = mapped_column(ForeignKey("calibration_versions.id", ondelete="CASCADE"), nullable=False)
    interval_start_mm: Mapped[int] = mapped_column(Integer, nullable=False)
    interval_end_mm: Mapped[int] = mapped_column(Integer, nullable=False)
    confidence: Mapped[float] = mapped_column(Numeric(7, 4), nullable=False)
    sample_count: Mapped[int] = mapped_column(Integer, nullable=False)
    variance: Mapped[float] = mapped_column(Numeric(18, 6), nullable=False)
    __table_args__ = (UniqueConstraint("version_id", "interval_start_mm", name="uq_confidence_version_interval"),)


class CalibrationTable(Base):
    __tablename__ = "calibration_tables"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    version_id: Mapped[int] = mapped_column(ForeignKey("calibration_versions.id", ondelete="CASCADE"), nullable=False)
    level_mm: Mapped[int] = mapped_column(Integer, nullable=False)
    liters: Mapped[float] = mapped_column(Numeric(14, 3), nullable=False)
    confidence: Mapped[float] = mapped_column(Numeric(7, 4), nullable=False)
    __table_args__ = (UniqueConstraint("version_id", "level_mm", name="uq_calibration_table_version_level"), Index("ix_calibration_table_version_level", "version_id", "level_mm"))


class CalibrationJob(TimestampMixin, Base):
    __tablename__ = "calibration_jobs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("learning_sessions.id", ondelete="CASCADE"), nullable=False)
    job_type: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="queued")
    payload_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    available_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    locked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error: Mapped[str | None] = mapped_column(Text)
    __table_args__ = (Index("ix_calibration_job_status_available", "status", "available_at"),)


class LegacyDeviceMapping(Base):
    __tablename__ = "legacy_device_mappings"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    station_id: Mapped[int] = mapped_column(ForeignKey("stations.id", ondelete="RESTRICT"), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(40), nullable=False)
    unified_entity_id: Mapped[int] = mapped_column(Integer, nullable=False)
    legacy_system: Mapped[str] = mapped_column(String(80), nullable=False)
    legacy_identifier: Mapped[str] = mapped_column(String(160), nullable=False)
    legacy_endpoint: Mapped[str | None] = mapped_column(String(500))
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    sync_status: Mapped[str] = mapped_column(String(30), default="pending", nullable=False)
    sync_error: Mapped[str | None] = mapped_column(Text)
    __table_args__ = (UniqueConstraint("station_id", "entity_type", "legacy_system", "legacy_identifier", name="uq_legacy_mapping_identity"), Index("ix_legacy_mapping_entity", "entity_type", "unified_entity_id"))


class DeviceReadingSnapshot(Base):
    __tablename__ = "device_reading_snapshots"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    station_id: Mapped[int] = mapped_column(ForeignKey("stations.id", ondelete="RESTRICT"), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(40), nullable=False)
    unified_entity_id: Mapped[int] = mapped_column(Integer, nullable=False)
    source: Mapped[str] = mapped_column(String(80), nullable=False)
    reading_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = (Index("ix_reading_snapshot_entity_time", "station_id", "entity_type", "unified_entity_id", "captured_at"),)


class ProtocolCommand(TimestampMixin, Base):
    __tablename__ = "protocol_commands"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    protocol_profile_id: Mapped[int] = mapped_column(ForeignKey("protocol_profiles.id", ondelete="RESTRICT"), nullable=False)
    command_key: Mapped[str] = mapped_column(String(80), nullable=False)
    name_ar: Mapped[str] = mapped_column(String(160), nullable=False)
    name_en: Mapped[str | None] = mapped_column(String(160))
    command_template: Mapped[str] = mapped_column(Text, nullable=False)
    command_type: Mapped[str] = mapped_column(String(30), default="MONITORING", nullable=False)
    direction: Mapped[str] = mapped_column(String(20), default="REQUEST_RESPONSE", nullable=False)
    operation: Mapped[str] = mapped_column(String(30), default="READ", nullable=False)
    request_prefix: Mapped[str] = mapped_column(String(160), default="", nullable=False)
    command_suffix: Mapped[str] = mapped_column(String(80), default="", nullable=False)
    encoding: Mapped[str] = mapped_column(String(30), default="ascii", nullable=False)
    response_type: Mapped[str] = mapped_column(String(30), default="bytes", nullable=False)
    response_pattern: Mapped[str | None] = mapped_column(Text)
    response_schema_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    error_mapping_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    response_expected: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    timeout_override: Mapped[float | None] = mapped_column(Numeric(8, 3))
    retries: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    retry_delay_ms: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    requires_ack: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    destructive: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    monitoring_allowed: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    control_allowed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    __table_args__ = (UniqueConstraint("protocol_profile_id", "command_key", name="uq_protocol_command_key"),)


class ProtocolVersion(Base):
    __tablename__ = "protocol_versions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    protocol_profile_id: Mapped[int] = mapped_column(ForeignKey("protocol_profiles.id", ondelete="CASCADE"), nullable=False)
    version: Mapped[str] = mapped_column(String(40), nullable=False)
    changelog: Mapped[str | None] = mapped_column(Text)
    definition_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    definition_hash: Mapped[str | None] = mapped_column(String(64))
    signature: Mapped[str | None] = mapped_column(Text)
    signature_algorithm: Mapped[str | None] = mapped_column(String(40))
    signing_key_id: Mapped[str | None] = mapped_column(String(100))
    signed_envelope_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    validation_report_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="DRAFT", nullable=False)
    created_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("unified_users.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = (UniqueConstraint("protocol_profile_id", "version", name="uq_protocol_version"),)


class ProtocolParameter(TimestampMixin, Base):
    __tablename__ = "protocol_parameters"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    protocol_profile_id: Mapped[int] = mapped_column(ForeignKey("protocol_profiles.id", ondelete="CASCADE"), nullable=False)
    parameter_key: Mapped[str] = mapped_column(String(100), nullable=False)
    label_ar: Mapped[str] = mapped_column(String(160), nullable=False)
    label_en: Mapped[str] = mapped_column(String(160), nullable=False)
    data_type: Mapped[str] = mapped_column(String(30), nullable=False)
    default_value_json: Mapped[object | None] = mapped_column(JSON)
    required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    secret: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    validation_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    parameter_scope: Mapped[str] = mapped_column(String(30), default="ASSIGNMENT", nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    __table_args__ = (UniqueConstraint("protocol_profile_id", "parameter_key", name="uq_protocol_parameter"),)


class ProtocolCapability(Base):
    __tablename__ = "protocol_capabilities"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    protocol_profile_id: Mapped[int] = mapped_column(ForeignKey("protocol_profiles.id", ondelete="CASCADE"), nullable=False)
    capability_code: Mapped[str] = mapped_column(String(100), nullable=False)
    capability_name: Mapped[str] = mapped_column(String(160), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    __table_args__ = (UniqueConstraint("protocol_profile_id", "capability_code", name="uq_protocol_capability"),)


class ProtocolAuditLog(Base):
    __tablename__ = "protocol_audit_logs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    protocol_profile_id: Mapped[int | None] = mapped_column(ForeignKey("protocol_profiles.id", ondelete="SET NULL"))
    action: Mapped[str] = mapped_column(String(80), nullable=False)
    before_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    after_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("unified_users.id", ondelete="SET NULL"))
    ip_address: Mapped[str | None] = mapped_column(String(80))
    correlation_id: Mapped[str | None] = mapped_column(String(80))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    __table_args__ = (Index("ix_protocol_audit_profile_created", "protocol_profile_id", "created_at"),)


class ProtocolResponseParser(TimestampMixin, Base):
    __tablename__ = "protocol_response_parsers"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    protocol_profile_id: Mapped[int] = mapped_column(ForeignKey("protocol_profiles.id", ondelete="RESTRICT"), nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    parser_type: Mapped[str] = mapped_column(String(40), nullable=False)
    pattern: Mapped[str | None] = mapped_column(Text)
    field_mapping_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    transformations_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    validation_rules_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class ChecksumProfile(TimestampMixin, Base):
    __tablename__ = "checksum_profiles"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(160), unique=True, nullable=False)
    checksum_type: Mapped[str] = mapped_column(String(40), nullable=False)
    parameters_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class ConnectionGroup(TimestampMixin, Base):
    __tablename__ = "connection_groups"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    station_id: Mapped[int] = mapped_column(ForeignKey("stations.id", ondelete="RESTRICT"), nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    connection_profile_id: Mapped[int] = mapped_column(ForeignKey("connection_profiles.id", ondelete="RESTRICT"), nullable=False)
    protocol_profile_id: Mapped[int] = mapped_column(ForeignKey("protocol_profiles.id", ondelete="RESTRICT"), nullable=False)
    group_key: Mapped[str] = mapped_column(String(500), nullable=False)
    scheduler_mode: Mapped[str] = mapped_column(String(30), nullable=False)
    poll_interval_seconds: Mapped[float] = mapped_column(Numeric(8, 3), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    shadow_only: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    __table_args__ = (UniqueConstraint("station_id", "group_key", name="uq_connection_group_key"),)


class ConnectionGroupDevice(Base):
    __tablename__ = "connection_group_devices"
    connection_group_id: Mapped[int] = mapped_column(ForeignKey("connection_groups.id", ondelete="CASCADE"), primary_key=True)
    assignment_id: Mapped[int] = mapped_column(ForeignKey("device_protocol_assignments.id", ondelete="CASCADE"), primary_key=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class ProtocolTestRun(Base):
    __tablename__ = "protocol_test_runs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    station_id: Mapped[int | None] = mapped_column(ForeignKey("stations.id", ondelete="SET NULL"))
    protocol_profile_id: Mapped[int | None] = mapped_column(ForeignKey("protocol_profiles.id", ondelete="SET NULL"))
    command_id: Mapped[int | None] = mapped_column(ForeignKey("protocol_commands.id", ondelete="SET NULL"))
    edge_device_id: Mapped[int | None] = mapped_column(ForeignKey("edge_devices.id", ondelete="SET NULL"))
    test_type: Mapped[str] = mapped_column(String(40), nullable=False)
    input_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    output_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    success: Mapped[bool] = mapped_column(Boolean, nullable=False)
    result: Mapped[str] = mapped_column(String(30), default="SIMULATED", nullable=False)
    duration_ms: Mapped[int | None] = mapped_column(Integer)
    correlation_id: Mapped[str | None] = mapped_column(String(80))
    error_message: Mapped[str | None] = mapped_column(Text)
    executed_by: Mapped[str | None] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class DeviceConnectionEvent(Base):
    __tablename__ = "device_connection_events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    station_id: Mapped[int] = mapped_column(ForeignKey("stations.id", ondelete="RESTRICT"), nullable=False)
    assignment_id: Mapped[int | None] = mapped_column(ForeignKey("device_protocol_assignments.id", ondelete="SET NULL"))
    event_type: Mapped[str] = mapped_column(String(80), nullable=False)
    health_state: Mapped[str] = mapped_column(String(30), nullable=False)
    message: Mapped[str | None] = mapped_column(Text)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class DeviceConfigurationVersion(Base):
    __tablename__ = "device_configuration_versions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    station_id: Mapped[int] = mapped_column(ForeignKey("stations.id", ondelete="RESTRICT"), nullable=False)
    device_category: Mapped[str] = mapped_column(String(40), nullable=False)
    device_id: Mapped[int] = mapped_column(Integer, nullable=False)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    configuration_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    changed_by: Mapped[str] = mapped_column(String(120), nullable=False)
    change_reason: Mapped[str | None] = mapped_column(Text)
    configuration_hash: Mapped[str] = mapped_column(String(128), default="", nullable=False)
    signature: Mapped[str] = mapped_column(Text, default="", nullable=False)
    signature_algorithm: Mapped[str] = mapped_column(String(40), default="HMAC-SHA256", nullable=False)
    signing_key_id: Mapped[str | None] = mapped_column(String(160))
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(32), default="PENDING_DELIVERY", nullable=False)
    delivery_status: Mapped[str] = mapped_column(String(32), default="PENDING", nullable=False)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    validated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    staged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    failed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    failure_code: Mapped[str | None] = mapped_column(String(80))
    failure_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    __table_args__ = (UniqueConstraint("station_id", "device_category", "device_id", "version_number", name="uq_device_config_version"),)


class LocationType(TimestampMixin, Base):
    __tablename__ = "location_types"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int | None] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"))
    code: Mapped[str] = mapped_column(String(60), nullable=False)
    name_ar: Mapped[str] = mapped_column(String(160), nullable=False)
    name_en: Mapped[str] = mapped_column(String(160), nullable=False)
    icon: Mapped[str] = mapped_column(String(60), default="map-pin", nullable=False)
    marker_color: Mapped[str] = mapped_column(String(20), default="#138bb8", nullable=False)
    show_on_map: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    configuration_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = (UniqueConstraint("company_id", "code", name="uq_location_type_company_code"),)


class Region(TimestampMixin, Base):
    __tablename__ = "regions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    country_code: Mapped[str] = mapped_column(String(2), nullable=False)
    code: Mapped[str] = mapped_column(String(40), nullable=False)
    name_ar: Mapped[str] = mapped_column(String(160), nullable=False)
    name_en: Mapped[str] = mapped_column(String(160), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    __table_args__ = (UniqueConstraint("country_code", "code", name="uq_region_country_code"),)


class City(TimestampMixin, Base):
    __tablename__ = "cities"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    region_id: Mapped[int] = mapped_column(ForeignKey("regions.id", ondelete="RESTRICT"), nullable=False)
    code: Mapped[str] = mapped_column(String(60), nullable=False)
    name_ar: Mapped[str] = mapped_column(String(160), nullable=False)
    name_en: Mapped[str] = mapped_column(String(160), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    __table_args__ = (UniqueConstraint("region_id", "code", name="uq_city_region_code"),)


class District(TimestampMixin, Base):
    __tablename__ = "districts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    city_id: Mapped[int] = mapped_column(ForeignKey("cities.id", ondelete="RESTRICT"), nullable=False)
    code: Mapped[str] = mapped_column(String(60), nullable=False)
    name_ar: Mapped[str] = mapped_column(String(160), nullable=False)
    name_en: Mapped[str] = mapped_column(String(160), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    __table_args__ = (UniqueConstraint("city_id", "code", name="uq_district_city_code"),)


class Location(TimestampMixin, Base):
    __tablename__ = "locations"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False)
    parent_location_id: Mapped[int | None] = mapped_column(ForeignKey("locations.id", ondelete="RESTRICT"))
    location_type_id: Mapped[int] = mapped_column(ForeignKey("location_types.id", ondelete="RESTRICT"), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(40), nullable=False)
    entity_id: Mapped[int | None] = mapped_column(Integer)
    code: Mapped[str] = mapped_column(String(80), nullable=False)
    name_ar: Mapped[str] = mapped_column(String(160), nullable=False)
    name_en: Mapped[str] = mapped_column(String(160), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="active", nullable=False)
    country_code: Mapped[str] = mapped_column(String(2), default="SA", nullable=False)
    region_id: Mapped[int | None] = mapped_column(ForeignKey("regions.id", ondelete="RESTRICT"))
    city_id: Mapped[int | None] = mapped_column(ForeignKey("cities.id", ondelete="RESTRICT"))
    district_id: Mapped[int | None] = mapped_column(ForeignKey("districts.id", ondelete="RESTRICT"))
    region_name: Mapped[str | None] = mapped_column(String(160))
    city_name: Mapped[str | None] = mapped_column(String(160))
    district_name: Mapped[str | None] = mapped_column(String(160))
    street: Mapped[str | None] = mapped_column(String(255))
    building_number: Mapped[str | None] = mapped_column(String(40))
    postal_code: Mapped[str | None] = mapped_column(String(20))
    additional_number: Mapped[str | None] = mapped_column(String(20))
    short_address: Mapped[str | None] = mapped_column(String(80))
    formatted_address: Mapped[str | None] = mapped_column(Text)
    google_place_id: Mapped[str | None] = mapped_column(String(255))
    google_maps_url: Mapped[str | None] = mapped_column(Text)
    latitude: Mapped[float | None] = mapped_column(Numeric(10, 8))
    longitude: Mapped[float | None] = mapped_column(Numeric(11, 8))
    plus_code: Mapped[str | None] = mapped_column(String(80))
    address_components: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    access_description: Mapped[str | None] = mapped_column(Text)
    timezone: Mapped[str] = mapped_column(String(80), default="Asia/Riyadh", nullable=False)
    phone: Mapped[str | None] = mapped_column(String(40))
    email: Mapped[str | None] = mapped_column(String(255))
    working_hours: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    manager_user_id: Mapped[int | None] = mapped_column(ForeignKey("unified_users.id", ondelete="SET NULL"))
    marker_icon: Mapped[str | None] = mapped_column(String(60))
    marker_color: Mapped[str | None] = mapped_column(String(20))
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("unified_users.id", ondelete="SET NULL"))
    updated_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("unified_users.id", ondelete="SET NULL"))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = (
        UniqueConstraint("company_id", "code", name="uq_location_company_code"),
        UniqueConstraint("company_id", "entity_type", "entity_id", name="uq_location_company_entity"),
        Index("ix_locations_tenant_filters", "company_id", "location_type_id", "status"),
        Index("ix_locations_bounds", "latitude", "longitude"),
    )


class LocationGeofence(TimestampMixin, Base):
    __tablename__ = "location_geofences"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    location_id: Mapped[int] = mapped_column(ForeignKey("locations.id", ondelete="CASCADE"), nullable=False)
    radius_meters: Mapped[float | None] = mapped_column(Numeric(12, 2))
    geojson: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    __table_args__ = (UniqueConstraint("location_id", name="uq_location_geofence"),)


class CompanyBranch(TimestampMixin, Base):
    __tablename__ = "company_branches"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False)
    location_id: Mapped[int] = mapped_column(ForeignKey("locations.id", ondelete="RESTRICT"), nullable=False)
    code: Mapped[str] = mapped_column(String(80), nullable=False)
    name_ar: Mapped[str] = mapped_column(String(160), nullable=False)
    name_en: Mapped[str] = mapped_column(String(160), nullable=False)
    branch_type: Mapped[str] = mapped_column(String(60), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="active", nullable=False)
    manager_user_id: Mapped[int | None] = mapped_column(ForeignKey("unified_users.id", ondelete="SET NULL"))
    opened_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    phone: Mapped[str | None] = mapped_column(String(40))
    email: Mapped[str | None] = mapped_column(String(255))
    working_hours: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = (UniqueConstraint("company_id", "code", name="uq_company_branch_code"),)


class CompanyLocationTypeSetting(TimestampMixin, Base):
    __tablename__ = "company_location_type_settings"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    location_type_id: Mapped[int] = mapped_column(ForeignKey("location_types.id", ondelete="CASCADE"), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    __table_args__ = (UniqueConstraint("company_id", "location_type_id", name="uq_company_location_type_setting"),)


class MapSetting(TimestampMixin, Base):
    __tablename__ = "map_settings"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int | None] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"))
    enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    environment: Mapped[str] = mapped_column(String(20), default="test", nullable=False)
    light_map_id: Mapped[str | None] = mapped_column(String(120))
    dark_map_id: Mapped[str | None] = mapped_column(String(120))
    default_latitude: Mapped[float] = mapped_column(Numeric(10, 8), default=24.7135517, nullable=False)
    default_longitude: Mapped[float] = mapped_column(Numeric(11, 8), default=46.6752957, nullable=False)
    default_zoom: Mapped[int] = mapped_column(Integer, default=6, nullable=False)
    default_map_type: Mapped[str] = mapped_column(String(20), default="roadmap", nullable=False)
    features_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    performance_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    allowed_domains: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    last_test_status: Mapped[str] = mapped_column(String(30), default="untested", nullable=False)
    last_tested_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    updated_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("unified_users.id", ondelete="SET NULL"))
    __table_args__ = (UniqueConstraint("company_id", name="uq_map_setting_company"),)


class MapApiCredential(TimestampMixin, Base):
    __tablename__ = "map_api_credentials"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int | None] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"))
    browser_key_encrypted: Mapped[str | None] = mapped_column(Text)
    server_key_encrypted: Mapped[str | None] = mapped_column(Text)
    browser_key_hint: Mapped[str | None] = mapped_column(String(40))
    server_key_hint: Mapped[str | None] = mapped_column(String(40))
    rotated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    updated_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("unified_users.id", ondelete="SET NULL"))
    __table_args__ = (UniqueConstraint("company_id", name="uq_map_credential_company"),)


class LocationImportJob(TimestampMixin, Base):
    __tablename__ = "location_import_jobs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    summary_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("unified_users.id", ondelete="SET NULL"))


class LocationAuditLog(Base):
    __tablename__ = "location_audit_logs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int | None] = mapped_column(ForeignKey("companies.id", ondelete="SET NULL"))
    location_id: Mapped[int | None] = mapped_column(ForeignKey("locations.id", ondelete="SET NULL"))
    user_id: Mapped[int | None] = mapped_column(ForeignKey("unified_users.id", ondelete="SET NULL"))
    action: Mapped[str] = mapped_column(String(80), nullable=False)
    old_values: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    new_values: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    ip_address: Mapped[str | None] = mapped_column(String(80))
    user_agent: Mapped[str | None] = mapped_column(String(300))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class EdgeRegistrationCounter(Base):
    __tablename__ = "edge_registration_counters"
    scope: Mapped[str] = mapped_column(String(30), primary_key=True)
    next_value: Mapped[int] = mapped_column(Integer, nullable=False, default=1)


class EdgeDevice(TimestampMixin, Base):
    __tablename__ = "edge_devices"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    device_uuid: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    registration_number: Mapped[str | None] = mapped_column(String(40), unique=True)
    installation_id: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    company_id: Mapped[int | None] = mapped_column(ForeignKey("companies.id", ondelete="RESTRICT"))
    station_id: Mapped[int | None] = mapped_column(ForeignKey("stations.id", ondelete="RESTRICT"))
    status: Mapped[str] = mapped_column(String(40), default="UNCLAIMED", nullable=False)
    connectivity_status: Mapped[str] = mapped_column(String(20), default="STALE", nullable=False)
    health_status: Mapped[str] = mapped_column(String(20), default="UNKNOWN", nullable=False)
    hardware_fingerprint_hash: Mapped[str | None] = mapped_column(String(128))
    public_key: Mapped[str] = mapped_column(Text, nullable=False)
    public_key_fingerprint: Mapped[str] = mapped_column(String(128), nullable=False)
    hostname: Mapped[str | None] = mapped_column(String(255))
    hardware_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    operating_system_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    capabilities_json: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    edge_version: Mapped[str | None] = mapped_column(String(80))
    configuration_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    activated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    suspended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error_code: Mapped[str | None] = mapped_column(String(80))
    last_error_message: Mapped[str | None] = mapped_column(Text)
    outbox_pending_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_commands_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    connected_devices_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_heartbeat_sequence: Mapped[int | None] = mapped_column(Integer)
    created_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("unified_users.id", ondelete="SET NULL"))
    updated_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("unified_users.id", ondelete="SET NULL"))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = (
        Index("ix_edge_devices_tenant_status", "company_id", "station_id", "status"),
        Index("ix_edge_devices_last_seen", "last_seen_at"),
    )


class EdgePairingSession(TimestampMixin, Base):
    __tablename__ = "edge_pairing_sessions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pairing_session_id: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    device_id: Mapped[int] = mapped_column(ForeignKey("edge_devices.id", ondelete="CASCADE"), nullable=False)
    pairing_code_hash: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    pairing_code_masked: Mapped[str] = mapped_column(String(30), nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="UNCLAIMED", nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    claimed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    activated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    attempt_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    claiming_user_id: Mapped[int | None] = mapped_column(ForeignKey("unified_users.id", ondelete="SET NULL"))
    company_id: Mapped[int | None] = mapped_column(ForeignKey("companies.id", ondelete="RESTRICT"))
    station_id: Mapped[int | None] = mapped_column(ForeignKey("stations.id", ondelete="RESTRICT"))
    requested_device_name: Mapped[str | None] = mapped_column(String(160))
    require_local_confirmation: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    request_identifier: Mapped[str | None] = mapped_column(String(80), unique=True)
    activation_delivery_secret_hash: Mapped[str | None] = mapped_column(String(128), unique=True)
    activation_delivery_secret_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    activation_delivery_secret_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    activation_delivery_secret_revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    activation_bundle_ready_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    activation_bundle_delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    activation_delivery_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_activation_delivery_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    correlation_id: Mapped[str] = mapped_column(String(80), nullable=False)
    last_error_code: Mapped[str | None] = mapped_column(String(80))
    __table_args__ = (Index("ix_edge_pairing_status_expiry", "status", "expires_at"),)


class EdgeEnrollmentRequest(Base):
    __tablename__ = "edge_enrollment_requests"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    device_id: Mapped[int] = mapped_column(ForeignKey("edge_devices.id", ondelete="CASCADE"), nullable=False)
    pairing_session_id: Mapped[int] = mapped_column(ForeignKey("edge_pairing_sessions.id", ondelete="CASCADE"), nullable=False)
    schema_version: Mapped[str] = mapped_column(String(20), nullable=False)
    payload_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    payload_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    source_ip: Mapped[str | None] = mapped_column(String(80))
    correlation_id: Mapped[str] = mapped_column(String(80), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(80), nullable=False)
    processing_status: Mapped[str] = mapped_column(String(30), default="ACCEPTED", nullable=False)
    error_code: Mapped[str | None] = mapped_column(String(80))
    __table_args__ = (UniqueConstraint("idempotency_key", name="uq_edge_enrollment_idempotency"),)


class EdgeAssignment(TimestampMixin, Base):
    __tablename__ = "edge_assignments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    device_id: Mapped[int] = mapped_column(ForeignKey("edge_devices.id", ondelete="CASCADE"), nullable=False)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False)
    station_id: Mapped[int] = mapped_column(ForeignKey("stations.id", ondelete="RESTRICT"), nullable=False)
    requested_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("unified_users.id", ondelete="SET NULL"))
    approved_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("unified_users.id", ondelete="SET NULL"))
    device_name: Mapped[str] = mapped_column(String(160), nullable=False)
    require_local_confirmation: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    local_confirmation_status: Mapped[str] = mapped_column(String(30), default="PENDING", nullable=False)
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    rejected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(30), default="PENDING", nullable=False)


class EdgeActivation(TimestampMixin, Base):
    __tablename__ = "edge_activations"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    device_id: Mapped[int] = mapped_column(ForeignKey("edge_devices.id", ondelete="CASCADE"), nullable=False)
    registration_number: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    activation_token_hash: Mapped[str | None] = mapped_column(String(128))
    activation_token_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    activation_bundle_version: Mapped[str] = mapped_column(String(20), default="1.0", nullable=False)
    configuration_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="ISSUED", nullable=False)
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    failed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    failure_reason: Mapped[str | None] = mapped_column(Text)
    encrypted_delivery_response: Mapped[str | None] = mapped_column(Text)
    delivery_response_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    delivery_idempotency_key: Mapped[str | None] = mapped_column(String(80), unique=True)
    delivery_request_hash: Mapped[str | None] = mapped_column(String(128))
    activation_token_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class EdgeCertificate(TimestampMixin, Base):
    __tablename__ = "edge_certificates"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    device_id: Mapped[int] = mapped_column(ForeignKey("edge_devices.id", ondelete="CASCADE"), nullable=False)
    certificate_serial: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    certificate_fingerprint: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    issuer: Mapped[str] = mapped_column(String(255), nullable=False)
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revocation_reason: Mapped[str | None] = mapped_column(Text)
    certificate_pem: Mapped[str] = mapped_column(Text, nullable=False)
    chain_pem: Mapped[str] = mapped_column(Text, nullable=False)
    __table_args__ = (Index("ix_edge_certificates_expiry", "status", "expires_at"),)


class EdgeHeartbeat(Base):
    __tablename__ = "edge_heartbeats"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    device_id: Mapped[int] = mapped_column(ForeignKey("edge_devices.id", ondelete="CASCADE"), nullable=False)
    sequence: Mapped[int] = mapped_column(BigInteger, nullable=False)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    edge_version: Mapped[str | None] = mapped_column(String(80))
    configuration_version: Mapped[int | None] = mapped_column(Integer)
    uptime_seconds: Mapped[int | None] = mapped_column(Integer)
    cpu_percent: Mapped[float | None] = mapped_column(Float)
    memory_percent: Mapped[float | None] = mapped_column(Float)
    disk_percent: Mapped[float | None] = mapped_column(Float)
    temperature: Mapped[float | None] = mapped_column(Float)
    health_status: Mapped[str] = mapped_column(String(20), nullable=False)
    payload_json_filtered: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    __table_args__ = (UniqueConstraint("device_id", "sequence", name="uq_edge_heartbeat_sequence"), Index("ix_edge_heartbeat_device_received", "device_id", "received_at"),)


class EdgeDeviceEvent(Base):
    __tablename__ = "edge_device_events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    device_id: Mapped[int] = mapped_column(ForeignKey("edge_devices.id", ondelete="CASCADE"), nullable=False)
    event_type: Mapped[str] = mapped_column(String(80), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    source: Mapped[str] = mapped_column(String(40), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    payload_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    acknowledged_by: Mapped[int | None] = mapped_column(ForeignKey("unified_users.id", ondelete="SET NULL"))


class EdgeAuditLog(Base):
    __tablename__ = "edge_audit_logs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    device_id: Mapped[int | None] = mapped_column(ForeignKey("edge_devices.id", ondelete="SET NULL"))
    company_id: Mapped[int | None] = mapped_column(ForeignKey("companies.id", ondelete="SET NULL"))
    user_id: Mapped[int | None] = mapped_column(ForeignKey("unified_users.id", ondelete="SET NULL"))
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    old_values: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    new_values: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    correlation_id: Mapped[str] = mapped_column(String(80), nullable=False)
    ip_address: Mapped[str | None] = mapped_column(String(80))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class EdgeIdempotencyRecord(Base):
    __tablename__ = "edge_idempotency_records"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    operation: Mapped[str] = mapped_column(String(50), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(80), nullable=False)
    payload_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    response_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    status_code: Mapped[int] = mapped_column(Integer, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    __table_args__ = (UniqueConstraint("operation", "idempotency_key", name="uq_edge_idempotency_operation_key"), Index("ix_edge_idempotency_expiry", "expires_at"),)


class EdgeRequestNonce(Base):
    __tablename__ = "edge_request_nonces"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    device_id: Mapped[int] = mapped_column(ForeignKey("edge_devices.id", ondelete="CASCADE"), nullable=False)
    operation: Mapped[str] = mapped_column(String(255), nullable=False)
    nonce: Mapped[str] = mapped_column(String(160), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    request_id: Mapped[str | None] = mapped_column(String(160))
    request_method: Mapped[str | None] = mapped_column(String(16))
    request_path: Mapped[str | None] = mapped_column(String(512))
    body_hash: Mapped[str | None] = mapped_column(String(128))
    __table_args__ = (
        UniqueConstraint("device_id", "operation", "nonce", name="uq_edge_nonce_device_operation"),
        Index("ix_edge_nonce_expiry", "expires_at"),
    )


class EdgeSerialPort(TimestampMixin, Base):
    __tablename__ = "edge_serial_ports"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    edge_device_id: Mapped[int] = mapped_column(ForeignKey("edge_devices.id", ondelete="CASCADE"), nullable=False)
    company_id: Mapped[int | None] = mapped_column(ForeignKey("companies.id", ondelete="SET NULL"))
    station_id: Mapped[int | None] = mapped_column(ForeignKey("stations.id", ondelete="SET NULL"))
    stable_identity: Mapped[str] = mapped_column(String(512), nullable=False)
    by_id_path: Mapped[str | None] = mapped_column(String(512))
    by_path: Mapped[str | None] = mapped_column(String(512))
    resolved_device: Mapped[str | None] = mapped_column(String(512))
    vendor: Mapped[str | None] = mapped_column(String(120))
    model: Mapped[str | None] = mapped_column(String(120))
    vendor_id: Mapped[str | None] = mapped_column(String(32))
    product_id: Mapped[str | None] = mapped_column(String(32))
    serial_number: Mapped[str | None] = mapped_column(String(160))
    driver: Mapped[str | None] = mapped_column(String(120))
    physical_path: Mapped[str | None] = mapped_column(String(512))
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="AVAILABLE")
    ownership_status: Mapped[str] = mapped_column(String(32), nullable=False, default="FREE")
    owner_process: Mapped[str | None] = mapped_column(String(160))
    owner_pid: Mapped[int | None] = mapped_column(Integer)
    owner_service: Mapped[str | None] = mapped_column(String(160))
    capabilities_json: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    disconnected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    friendly_name: Mapped[str | None] = mapped_column(String(160))
    function_label: Mapped[str | None] = mapped_column(String(40))
    __table_args__ = (UniqueConstraint("edge_device_id", "stable_identity", name="uq_edge_serial_port_identity"),)


class EdgePortInventorySync(Base):
    __tablename__ = "edge_port_inventory_syncs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    edge_device_id: Mapped[int] = mapped_column(ForeignKey("edge_devices.id", ondelete="CASCADE"), nullable=False)
    sync_id: Mapped[str] = mapped_column(String(100), nullable=False)
    inventory_version: Mapped[int] = mapped_column(Integer, nullable=False)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    port_count: Mapped[int] = mapped_column(Integer, nullable=False)
    checksum: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="ACCEPTED")
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    __table_args__ = (UniqueConstraint("edge_device_id", "sync_id", name="uq_edge_inventory_sync"),)


class CloudBusDevice(TimestampMixin, Base):
    __tablename__ = "cloud_bus_devices"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cloud_device_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False)
    station_id: Mapped[int] = mapped_column(ForeignKey("stations.id", ondelete="RESTRICT"), nullable=False)
    edge_device_id: Mapped[int] = mapped_column(ForeignKey("edge_devices.id", ondelete="RESTRICT"), nullable=False)
    serial_port_id: Mapped[int] = mapped_column(ForeignKey("edge_serial_ports.id", ondelete="RESTRICT"), nullable=False)
    device_type: Mapped[str] = mapped_column(String(50), nullable=False)
    device_name: Mapped[str] = mapped_column(String(160), nullable=False)
    logical_number: Mapped[str | None] = mapped_column(String(80))
    protocol_id: Mapped[int] = mapped_column(ForeignKey("protocol_profiles.id", ondelete="RESTRICT"), nullable=False)
    protocol_version_id: Mapped[int | None] = mapped_column(ForeignKey("protocol_versions.id", ondelete="RESTRICT"))
    protocol_code: Mapped[str | None] = mapped_column(String(100))
    protocol_version: Mapped[str | None] = mapped_column(String(40))
    protocol_hash: Mapped[str | None] = mapped_column(String(64))
    device_address: Mapped[str] = mapped_column(String(100), nullable=False)
    bus_config_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    protocol_config_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    capabilities_json: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    polling_config_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    command_permissions_json: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="STAGED")
    deployment_status: Mapped[str] = mapped_column(String(40), nullable=False, default="DRAFT")
    configuration_status: Mapped[str] = mapped_column(String(40), nullable=False, default="NOT_CONFIGURED")
    activation_status: Mapped[str] = mapped_column(String(32), nullable=False, default="BLOCKED")
    activation_blocked_reason: Mapped[str | None] = mapped_column(String(120))
    offline_ready: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    hardware_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    last_configuration_version_id: Mapped[int | None] = mapped_column(ForeignKey("device_configuration_versions.id", ondelete="SET NULL"))
    last_delivery_id: Mapped[str | None] = mapped_column(String(100))
    last_edge_ack_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    active_config_version_id: Mapped[int | None] = mapped_column(Integer)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("unified_users.id", ondelete="SET NULL"))
    __table_args__ = (
        Index(
            "uq_cloud_bus_device_active_address",
            "edge_device_id", "serial_port_id", "protocol_id", "device_address",
            unique=True,
            postgresql_where=text(
                "status NOT IN ('DECOMMISSIONED', 'SUPERSEDED', 'DELETED')"
            ),
            sqlite_where=text(
                "status NOT IN ('DECOMMISSIONED', 'SUPERSEDED', 'DELETED')"
            ),
        ),
    )


class DeviceDeploymentEvent(Base):
    __tablename__ = "device_deployment_events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cloud_bus_device_id: Mapped[int] = mapped_column(ForeignKey("cloud_bus_devices.id", ondelete="CASCADE"), nullable=False)
    edge_device_id: Mapped[int] = mapped_column(ForeignKey("edge_devices.id", ondelete="CASCADE"), nullable=False)
    configuration_version_id: Mapped[int | None] = mapped_column(ForeignKey("device_configuration_versions.id", ondelete="SET NULL"))
    delivery_id: Mapped[str | None] = mapped_column(String(100))
    event_type: Mapped[str] = mapped_column(String(60), nullable=False)
    source: Mapped[str] = mapped_column(String(60), nullable=False)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    __table_args__ = (
        Index("ix_device_deployment_event_device_time", "cloud_bus_device_id", "occurred_at"),
    )


class EdgeConfigurationDelivery(Base):
    __tablename__ = "edge_configuration_deliveries"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    configuration_version_id: Mapped[int] = mapped_column(ForeignKey("device_configuration_versions.id", ondelete="CASCADE"), nullable=False)
    edge_device_id: Mapped[int] = mapped_column(ForeignKey("edge_devices.id", ondelete="CASCADE"), nullable=False)
    delivery_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="PENDING")
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    next_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    response_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    error_code: Mapped[str | None] = mapped_column(String(80))
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)


class EdgeProtocolDelivery(Base):
    __tablename__ = "edge_protocol_deliveries"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    delivery_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    edge_device_id: Mapped[int] = mapped_column(ForeignKey("edge_devices.id", ondelete="CASCADE"), nullable=False)
    protocol_profile_id: Mapped[int] = mapped_column(ForeignKey("protocol_profiles.id", ondelete="RESTRICT"), nullable=False)
    protocol_version_id: Mapped[int] = mapped_column(ForeignKey("protocol_versions.id", ondelete="RESTRICT"), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="PENDING")
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    response_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    error_code: Mapped[str | None] = mapped_column(String(100))
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)
    __table_args__ = (
        UniqueConstraint("edge_device_id", "protocol_version_id", name="uq_edge_protocol_delivery_version"),
        Index("ix_edge_protocol_delivery_status", "edge_device_id", "status"),
    )


class EdgeInstalledProtocol(Base):
    __tablename__ = "edge_installed_protocols"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    edge_device_id: Mapped[int] = mapped_column(ForeignKey("edge_devices.id", ondelete="CASCADE"), nullable=False)
    protocol_profile_id: Mapped[int] = mapped_column(ForeignKey("protocol_profiles.id", ondelete="RESTRICT"), nullable=False)
    protocol_version_id: Mapped[int] = mapped_column(ForeignKey("protocol_versions.id", ondelete="RESTRICT"), nullable=False)
    protocol_code: Mapped[str] = mapped_column(String(100), nullable=False)
    version: Mapped[str] = mapped_column(String(40), nullable=False)
    definition_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="VERIFIED")
    verified_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    last_reported_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    __table_args__ = (
        UniqueConstraint("edge_device_id", "protocol_version_id", name="uq_edge_installed_protocol"),
        Index("ix_edge_installed_protocol_code", "edge_device_id", "protocol_code"),
    )


class DeviceDeploymentPlan(Base):
    __tablename__ = "device_deployment_plans"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    assignment_id: Mapped[int] = mapped_column(ForeignKey("device_protocol_assignments.id", ondelete="CASCADE"), unique=True, nullable=False)
    edge_device_id: Mapped[int] = mapped_column(ForeignKey("edge_devices.id", ondelete="CASCADE"), nullable=False)
    protocol_version_id: Mapped[int] = mapped_column(ForeignKey("protocol_versions.id", ondelete="RESTRICT"), nullable=False)
    state: Mapped[str] = mapped_column(String(40), nullable=False, default="WAITING_FOR_PROTOCOL")
    dependency_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    configuration_version_id: Mapped[int | None] = mapped_column(ForeignKey("device_configuration_versions.id", ondelete="SET NULL"))
    activation_blocked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)


class EdgeIngestedEvent(Base):
    __tablename__ = "edge_ingested_events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    edge_device_id: Mapped[int] = mapped_column(ForeignKey("edge_devices.id", ondelete="CASCADE"), nullable=False)
    event_id: Mapped[str] = mapped_column(String(80), nullable=False)
    event_type: Mapped[str] = mapped_column(String(40), nullable=False)
    station_id: Mapped[int | None] = mapped_column(ForeignKey("stations.id", ondelete="RESTRICT"))
    device_id: Mapped[str | None] = mapped_column(String(100))
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    priority: Mapped[str] = mapped_column(String(20), nullable=False)
    payload_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    __table_args__ = (
        UniqueConstraint("edge_device_id", "event_id", name="uq_edge_ingested_event"),
        Index("ix_edge_ingested_event_sequence", "edge_device_id", "sequence"),
    )


class ConfigurationSigningKey(Base):
    __tablename__ = "configuration_signing_keys"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    key_id: Mapped[str] = mapped_column(String(160), unique=True, nullable=False)
    algorithm: Mapped[str] = mapped_column(String(40), nullable=False, default="Ed25519")
    public_key: Mapped[str] = mapped_column(Text, nullable=False)
    private_key_reference: Mapped[str] = mapped_column(String(512), nullable=False)
    fingerprint_sha256: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="ACTIVE")
    valid_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    valid_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    retired_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_by: Mapped[str | None] = mapped_column(String(120))
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)


class EdgeContractCounter(Base):
    __tablename__ = "edge_contract_counters"
    scope: Mapped[str] = mapped_column(String(40), primary_key=True)
    next_value: Mapped[int] = mapped_column(Integer, nullable=False, default=1)


class EdgeContract(TimestampMixin, Base):
    __tablename__ = "edge_contracts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    contract_code: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    edge_device_id: Mapped[int] = mapped_column(
        ForeignKey("edge_devices.id", ondelete="RESTRICT"), unique=True, nullable=False
    )
    current_version_id: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="DRAFT")
    created_by: Mapped[int | None] = mapped_column(
        ForeignKey("unified_users.id", ondelete="SET NULL")
    )


class EdgeContractVersion(Base):
    __tablename__ = "edge_contract_versions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    contract_id: Mapped[int] = mapped_column(
        ForeignKey("edge_contracts.id", ondelete="RESTRICT"), nullable=False
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    schema_version: Mapped[str] = mapped_column(String(20), nullable=False)
    definition_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    definition_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    signed_envelope_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    signature: Mapped[str] = mapped_column(Text, nullable=False)
    signature_algorithm: Mapped[str] = mapped_column(String(40), nullable=False)
    signing_key_id: Mapped[str] = mapped_column(String(160), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="DRAFT")
    issued_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    effective_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_by: Mapped[int | None] = mapped_column(
        ForeignKey("unified_users.id", ondelete="SET NULL")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    activated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    superseded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = (
        UniqueConstraint("contract_id", "version_number", name="uq_edge_contract_version"),
    )


class EdgeContractDelivery(Base):
    __tablename__ = "edge_contract_deliveries"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    delivery_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    contract_id: Mapped[int] = mapped_column(
        ForeignKey("edge_contracts.id", ondelete="RESTRICT"), nullable=False
    )
    contract_version_id: Mapped[int] = mapped_column(
        ForeignKey("edge_contract_versions.id", ondelete="RESTRICT"), nullable=False
    )
    edge_device_id: Mapped[int] = mapped_column(
        ForeignKey("edge_devices.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(64), nullable=False, default="PENDING")
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    error_code: Mapped[str | None] = mapped_column(String(100))
    error_message: Mapped[str | None] = mapped_column(Text)
    __table_args__ = (
        Index("ix_edge_contract_delivery_pending", "edge_device_id", "status"),
    )


class HardwareActivationDelivery(TimestampMixin, Base):
    __tablename__ = "hardware_activation_deliveries"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    delivery_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    edge_device_id: Mapped[int] = mapped_column(
        ForeignKey("edge_devices.id", ondelete="CASCADE"), nullable=False
    )
    device_id: Mapped[int] = mapped_column(
        ForeignKey("cloud_bus_devices.id", ondelete="RESTRICT"), nullable=False
    )
    configuration_version_id: Mapped[int] = mapped_column(
        ForeignKey("device_configuration_versions.id", ondelete="RESTRICT"),
        nullable=False,
    )
    contract_version_id: Mapped[int] = mapped_column(
        ForeignKey("edge_contract_versions.id", ondelete="RESTRICT"), nullable=False
    )
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    payload_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    payload_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    signed_envelope_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    signature: Mapped[str] = mapped_column(Text, nullable=False)
    signature_algorithm: Mapped[str] = mapped_column(String(40), nullable=False)
    signing_key_id: Mapped[str] = mapped_column(String(160), nullable=False)
    status: Mapped[str] = mapped_column(String(64), nullable=False, default="PENDING")
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_code: Mapped[str | None] = mapped_column(String(100))
    error_message: Mapped[str | None] = mapped_column(Text)
    result_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    __table_args__ = (
        Index("ix_hardware_activation_pending", "edge_device_id", "status"),
    )


class HardwareDiagnosticRun(TimestampMixin, Base):
    __tablename__ = "hardware_diagnostic_runs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    diagnostic_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    edge_device_id: Mapped[int] = mapped_column(
        ForeignKey("edge_devices.id", ondelete="CASCADE"), nullable=False
    )
    device_type: Mapped[str] = mapped_column(String(40), nullable=False)
    stable_port_identity: Mapped[str] = mapped_column(String(512), nullable=False)
    protocol_version_id: Mapped[int] = mapped_column(
        ForeignKey("protocol_versions.id", ondelete="RESTRICT"), nullable=False
    )
    probe_serial: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="PENDING")
    requested_by: Mapped[int | None] = mapped_column(
        ForeignKey("unified_users.id", ondelete="SET NULL")
    )
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    edge_received_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    elapsed_ms: Mapped[float | None] = mapped_column(Numeric(12, 3))
    parser_status: Mapped[str | None] = mapped_column(String(80))
    result_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    error_code: Mapped[str | None] = mapped_column(String(100))
    error_message: Mapped[str | None] = mapped_column(Text)
    payload_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    payload_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    signed_envelope_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    signature: Mapped[str] = mapped_column(Text, nullable=False)
    signature_algorithm: Mapped[str] = mapped_column(String(40), nullable=False)
    signing_key_id: Mapped[str] = mapped_column(String(160), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    __table_args__ = (
        Index("ix_hardware_diagnostic_pending", "edge_device_id", "status"),
        Index("ix_hardware_diagnostic_probe", "edge_device_id", "probe_serial"),
    )
