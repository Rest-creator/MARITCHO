"""review status for identity documents (ADR-010)

Revision ID: 8c9d0e1f2a3b
Revises: 7b8c9d0e1f2a
Create Date: 2026-11-26 10:00:00.000000

Badges now follow an OPS review, not the mere presence of a photo. Photos
already on file are kept (private, owner + OPS only) and marked PENDING, so
their grade and Police Cleared badge wait for a reviewer.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "8c9d0e1f2a3b"
down_revision: str | Sequence[str] | None = "7b8c9d0e1f2a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    add = op.add_column
    add("worker_vetting", sa.Column("id_status", sa.String(length=20), nullable=True))
    add("worker_vetting", sa.Column("id_reviewed_at", sa.DateTime(timezone=True), nullable=True))
    add(
        "worker_vetting",
        sa.Column("id_reviewed_by", postgresql.UUID(as_uuid=True), nullable=True),
    )
    add("worker_vetting", sa.Column("id_rejection_reason", sa.String(length=255), nullable=True))
    add("worker_vetting", sa.Column("id_verified_name", sa.String(length=120), nullable=True))
    add("worker_vetting", sa.Column("id_number_hash", sa.String(length=64), nullable=True))
    add(
        "worker_vetting",
        sa.Column("police_clearance_status", sa.String(length=20), nullable=True),
    )
    add(
        "worker_vetting",
        sa.Column("police_clearance_reviewed_at", sa.DateTime(timezone=True), nullable=True),
    )
    add(
        "worker_vetting",
        sa.Column("police_clearance_reviewed_by", postgresql.UUID(as_uuid=True), nullable=True),
    )
    add(
        "worker_vetting",
        sa.Column("police_clearance_rejection_reason", sa.String(length=255), nullable=True),
    )
    add("worker_vetting", sa.Column("police_clearance_issued_on", sa.Date(), nullable=True))
    add("worker_vetting", sa.Column("police_clearance_expires_on", sa.Date(), nullable=True))
    op.create_foreign_key(
        "fk_worker_vetting_id_reviewed_by",
        "worker_vetting",
        "persons",
        ["id_reviewed_by"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_worker_vetting_police_clearance_reviewed_by",
        "worker_vetting",
        "persons",
        ["police_clearance_reviewed_by"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_unique_constraint(
        "uq_worker_vetting_id_number_hash", "worker_vetting", ["id_number_hash"]
    )
    # Photos already on file were never checked: queue them for review.
    op.execute("UPDATE worker_vetting SET id_status = 'PENDING' WHERE id_photo_url IS NOT NULL")
    op.execute(
        "UPDATE worker_vetting SET police_clearance_status = 'PENDING' "
        "WHERE police_clearance_url IS NOT NULL"
    )
    # IDENTIFIED/APPRENTICE grades were earned by an unchecked photo; drop them
    # back to REGISTERED until the ID is approved. Vouch-earned grades stay.
    op.execute(
        "UPDATE standings SET grade = 'REGISTERED' WHERE grade IN ('IDENTIFIED', 'APPRENTICE')"
    )


def downgrade() -> None:
    op.drop_constraint("uq_worker_vetting_id_number_hash", "worker_vetting", type_="unique")
    op.drop_constraint(
        "fk_worker_vetting_police_clearance_reviewed_by", "worker_vetting", type_="foreignkey"
    )
    op.drop_constraint("fk_worker_vetting_id_reviewed_by", "worker_vetting", type_="foreignkey")
    for column in (
        "police_clearance_expires_on",
        "police_clearance_issued_on",
        "police_clearance_rejection_reason",
        "police_clearance_reviewed_by",
        "police_clearance_reviewed_at",
        "police_clearance_status",
        "id_number_hash",
        "id_verified_name",
        "id_rejection_reason",
        "id_reviewed_by",
        "id_reviewed_at",
        "id_status",
    ):
        op.drop_column("worker_vetting", column)
