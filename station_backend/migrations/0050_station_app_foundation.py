"""Station employee application foundation.

Revision ID: 0050_station_app_foundation
Revises: 0049_customer_single_auth
"""

from alembic import op
import sqlalchemy as sa


revision = "0050_station_app_foundation"
down_revision = "0049_customer_single_auth"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "station_app_employees",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("public_id", sa.String(36), nullable=False, unique=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("station_id", sa.Integer(), sa.ForeignKey("stations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("password_lookup_digest", sa.String(64), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("failed_login_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("locked_until", sa.DateTime(timezone=True)),
        sa.Column("last_login_at", sa.DateTime(timezone=True)),
        sa.Column("created_by_user_id", sa.Integer(), sa.ForeignKey("unified_users.id", ondelete="SET NULL")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_station_app_employee_station", "station_app_employees", ["station_id", "enabled"])
    op.create_index("ix_station_app_employee_company", "station_app_employees", ["company_id"])

    op.create_table(
        "station_app_sessions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("session_id", sa.String(96), nullable=False, unique=True),
        sa.Column("employee_id", sa.Integer(), sa.ForeignKey("station_app_employees.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("ip_address", sa.String(80)),
        sa.Column("user_agent", sa.String(500)),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_used_at", sa.DateTime(timezone=True)),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
        sa.Column("revoke_reason", sa.String(80)),
    )
    op.create_index("ix_station_app_session_employee", "station_app_sessions", ["employee_id", "expires_at"])

    op.create_table(
        "station_app_qr_resolutions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("public_id", sa.String(36), nullable=False, unique=True),
        sa.Column("employee_id", sa.Integer(), sa.ForeignKey("station_app_employees.id", ondelete="CASCADE"), nullable=False),
        sa.Column("qr_token_id", sa.Integer(), sa.ForeignKey("customer_qr_tokens.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("station_id", sa.Integer(), sa.ForeignKey("stations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("pump_id", sa.Integer(), sa.ForeignKey("pumps.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("nozzle_id", sa.Integer(), sa.ForeignKey("nozzles.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_station_app_qr_employee", "station_app_qr_resolutions", ["employee_id", "expires_at"])

    op.create_table(
        "station_app_fueling_sessions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("public_id", sa.String(36), nullable=False, unique=True),
        sa.Column("idempotency_key", sa.String(190), nullable=False, unique=True),
        sa.Column("employee_id", sa.Integer(), sa.ForeignKey("station_app_employees.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("station_id", sa.Integer(), sa.ForeignKey("stations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("shift_id", sa.Integer(), sa.ForeignKey("shift_sessions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("pump_id", sa.Integer(), sa.ForeignKey("pumps.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("nozzle_id", sa.Integer(), sa.ForeignKey("nozzles.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("qr_resolution_id", sa.Integer(), sa.ForeignKey("station_app_qr_resolutions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("delivery_id", sa.String(80), unique=True),
        sa.Column("sale_transaction_id", sa.Integer(), sa.ForeignKey("sale_transactions.id", ondelete="SET NULL"), unique=True),
        sa.Column("requested_amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("actual_amount", sa.Numeric(14, 2)),
        sa.Column("actual_liters", sa.Numeric(14, 3)),
        sa.Column("unit_price", sa.Numeric(12, 3), nullable=False),
        sa.Column("fuel_code", sa.String(40), nullable=False),
        sa.Column("status", sa.String(40), nullable=False, server_default="AUTHORIZATION_QUEUED"),
        sa.Column("payment_method", sa.String(20)),
        sa.Column("payment_other_reason", sa.Text()),
        sa.Column("payment_recorded_at", sa.DateTime(timezone=True)),
        sa.Column("authorized_at", sa.DateTime(timezone=True)),
        sa.Column("fueling_started_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("failure_code", sa.String(100)),
        sa.Column("failure_message", sa.String(500)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_station_app_fueling_employee", "station_app_fueling_sessions", ["employee_id", "created_at"])
    op.create_index("ix_station_app_fueling_station", "station_app_fueling_sessions", ["station_id", "created_at"])
    op.create_index(
        "uq_station_app_active_nozzle",
        "station_app_fueling_sessions",
        ["station_id", "pump_id", "nozzle_id"],
        unique=True,
        postgresql_where=sa.text("status IN ('AUTHORIZATION_QUEUED','EDGE_RECEIVED','PUMP_WAITING','PUMP_AUTHORIZED','FUELING','COMPLETED_AWAITING_PAYMENT')"),
    )

    op.create_table(
        "station_app_audit_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("employee_id", sa.Integer(), sa.ForeignKey("station_app_employees.id", ondelete="SET NULL")),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="SET NULL")),
        sa.Column("station_id", sa.Integer(), sa.ForeignKey("stations.id", ondelete="SET NULL")),
        sa.Column("fueling_session_id", sa.Integer(), sa.ForeignKey("station_app_fueling_sessions.id", ondelete="SET NULL")),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("correlation_id", sa.String(64), nullable=False),
        sa.Column("ip_address", sa.String(80)),
        sa.Column("details_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_station_app_audit_employee", "station_app_audit_events", ["employee_id", "created_at"])


def downgrade():
    op.drop_table("station_app_audit_events")
    op.drop_table("station_app_fueling_sessions")
    op.drop_table("station_app_qr_resolutions")
    op.drop_table("station_app_sessions")
    op.drop_table("station_app_employees")

