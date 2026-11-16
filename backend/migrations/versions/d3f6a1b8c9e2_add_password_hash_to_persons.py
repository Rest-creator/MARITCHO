"""Add password_hash to persons, drop otp_requests (phone+password auth replaces OTP)."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "d3f6a1b8c9e2"
down_revision: Union[str, Sequence[str], None] = "c1e7b2f4a901"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("persons", sa.Column("password_hash", sa.String(255), nullable=True))
    op.drop_index("ix_otp_requests_phone_created", table_name="otp_requests")
    op.drop_table("otp_requests")


def downgrade() -> None:
    op.create_table(
        "otp_requests",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("phone", sa.String(20), nullable=False),
        sa.Column("ip_address", sa.String(64), nullable=False),
        sa.Column("code_hash", sa.String(255), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_otp_requests_phone_created", "otp_requests", ["phone", "created_at"])
    op.drop_column("persons", "password_hash")
