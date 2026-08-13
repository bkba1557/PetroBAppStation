"""Station employee fueling cancellation delivery.

Revision ID: 0051_station_app_cancel
Revises: 0050_station_app_foundation
"""

from alembic import op
import sqlalchemy as sa


revision = "0051_station_app_cancel"
down_revision = "0050_station_app_foundation"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "station_app_fueling_sessions",
        sa.Column(
            "fueling_mode",
            sa.String(20),
            nullable=False,
            server_default="PRESET",
        ),
    )
    op.add_column(
        "station_app_fueling_sessions",
        sa.Column("cancellation_delivery_id", sa.String(80)),
    )
    op.add_column(
        "station_app_fueling_sessions",
        sa.Column("cancel_requested_at", sa.DateTime(timezone=True)),
    )
    op.add_column(
        "station_app_fueling_sessions",
        sa.Column("cancelled_at", sa.DateTime(timezone=True)),
    )
    op.create_unique_constraint(
        "uq_station_app_cancel_delivery",
        "station_app_fueling_sessions",
        ["cancellation_delivery_id"],
    )
    op.drop_index(
        "uq_station_app_active_nozzle",
        table_name="station_app_fueling_sessions",
    )
    op.create_index(
        "uq_station_app_active_nozzle",
        "station_app_fueling_sessions",
        ["station_id", "pump_id", "nozzle_id"],
        unique=True,
        postgresql_where=sa.text(
            "status IN ('AUTHORIZATION_QUEUED','EDGE_RECEIVED','PUMP_WAITING',"
            "'PUMP_AUTHORIZED','FUELING','COMPLETED_AWAITING_PAYMENT',"
            "'CANCELLATION_QUEUED','CANCELLATION_FAILED')"
        ),
    )


def downgrade():
    op.drop_index(
        "uq_station_app_active_nozzle",
        table_name="station_app_fueling_sessions",
    )
    op.create_index(
        "uq_station_app_active_nozzle",
        "station_app_fueling_sessions",
        ["station_id", "pump_id", "nozzle_id"],
        unique=True,
        postgresql_where=sa.text(
            "status IN ('AUTHORIZATION_QUEUED','EDGE_RECEIVED','PUMP_WAITING',"
            "'PUMP_AUTHORIZED','FUELING','COMPLETED_AWAITING_PAYMENT')"
        ),
    )
    op.drop_constraint(
        "uq_station_app_cancel_delivery",
        "station_app_fueling_sessions",
        type_="unique",
    )
    op.drop_column("station_app_fueling_sessions", "cancelled_at")
    op.drop_column("station_app_fueling_sessions", "cancel_requested_at")
    op.drop_column("station_app_fueling_sessions", "cancellation_delivery_id")
    op.drop_column("station_app_fueling_sessions", "fueling_mode")
