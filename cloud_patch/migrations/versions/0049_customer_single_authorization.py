"""One active fueling and one hardware authorization per customer session.

Revision ID: 0049_customer_single_auth
Revises: 0048_customer_nozzle_qr
"""

from alembic import op


revision = "0049_customer_single_auth"
down_revision = "0048_customer_nozzle_qr"
branch_labels = None
depends_on = None

def upgrade():
    op.create_unique_constraint(
        "uq_pump_command_fueling_session", "pump_commands", ["fueling_session_id"])


def downgrade():
    op.drop_constraint(
        "uq_pump_command_fueling_session", "pump_commands", type_="unique")
