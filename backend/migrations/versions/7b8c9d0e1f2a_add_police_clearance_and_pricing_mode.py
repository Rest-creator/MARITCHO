"""add police_clearance to worker_vetting and pricing_mode to jobs

Revision ID: 7b8c9d0e1f2a
Revises: 5a7e2c9d4b13
Create Date: 2026-11-23 21:35:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "7b8c9d0e1f2a"
down_revision: str | Sequence[str] | None = "5a7e2c9d4b13"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "worker_vetting",
        sa.Column("police_clearance_url", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "worker_vetting",
        sa.Column("police_clearance_submitted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "jobs",
        sa.Column(
            "pricing_mode",
            sa.String(length=20),
            nullable=False,
            server_default="NEGOTIABLE",
        ),
    )


def downgrade() -> None:
    op.drop_column("jobs", "pricing_mode")
    op.drop_column("worker_vetting", "police_clearance_submitted_at")
    op.drop_column("worker_vetting", "police_clearance_url")
