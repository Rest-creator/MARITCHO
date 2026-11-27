"""two-way, double-blind reviews with replies and reports (ADR-011)

Revision ID: 9d0e1f2a3b4c
Revises: 8c9d0e1f2a3b
Create Date: 2026-11-26 14:00:00.000000

Existing reviews were all employer -> worker and were already public, so they
are backfilled as BUYER_TO_WORKER, authored by the buyer, about the worker,
and published at their creation time.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "9d0e1f2a3b4c"
down_revision: str | Sequence[str] | None = "8c9d0e1f2a3b"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_NEW_TAGS = ("PAID_ON_TIME", "JOB_AS_DESCRIBED", "RESPECTFUL", "SAFE_WORKPLACE")


def upgrade() -> None:
    for tag in _NEW_TAGS:
        op.execute(f"ALTER TYPE reviewtagenum ADD VALUE IF NOT EXISTS '{tag}'")

    add = op.add_column
    add(
        "reviews",
        sa.Column(
            "direction",
            sa.String(length=20),
            nullable=False,
            server_default="BUYER_TO_WORKER",
        ),
    )
    add("reviews", sa.Column("author_id", postgresql.UUID(as_uuid=True), nullable=True))
    add("reviews", sa.Column("subject_id", postgresql.UUID(as_uuid=True), nullable=True))
    add("reviews", sa.Column("visible_after", sa.DateTime(timezone=True), nullable=True))
    add("reviews", sa.Column("published_at", sa.DateTime(timezone=True), nullable=True))
    add(
        "reviews",
        sa.Column("had_dispute", sa.Boolean(), nullable=False, server_default="false"),
    )
    add("reviews", sa.Column("reply", sa.Text(), nullable=True))
    add("reviews", sa.Column("replied_at", sa.DateTime(timezone=True), nullable=True))
    add("reviews", sa.Column("reported_at", sa.DateTime(timezone=True), nullable=True))
    add("reviews", sa.Column("reported_by", postgresql.UUID(as_uuid=True), nullable=True))
    add("reviews", sa.Column("report_reason", sa.String(length=255), nullable=True))
    add("reviews", sa.Column("hidden_at", sa.DateTime(timezone=True), nullable=True))
    add("reviews", sa.Column("moderated_by", postgresql.UUID(as_uuid=True), nullable=True))
    add("reviews", sa.Column("moderated_at", sa.DateTime(timezone=True), nullable=True))

    op.execute(
        "UPDATE reviews SET author_id = buyer_id, subject_id = worker_id, "
        "visible_after = created_at, published_at = created_at"
    )
    op.alter_column("reviews", "author_id", nullable=False)
    op.alter_column("reviews", "subject_id", nullable=False)
    op.alter_column("reviews", "visible_after", nullable=False)

    for column, name in (
        ("author_id", "fk_reviews_author_id"),
        ("subject_id", "fk_reviews_subject_id"),
    ):
        op.create_foreign_key(name, "reviews", "persons", [column], ["id"])
    for column, name in (
        ("reported_by", "fk_reviews_reported_by"),
        ("moderated_by", "fk_reviews_moderated_by"),
    ):
        op.create_foreign_key(name, "reviews", "persons", [column], ["id"], ondelete="SET NULL")

    op.drop_constraint("uq_reviews_job", "reviews", type_="unique")
    op.create_unique_constraint("uq_reviews_job_direction", "reviews", ["job_id", "direction"])
    op.create_index("ix_reviews_subject_direction", "reviews", ["subject_id", "direction"])


def downgrade() -> None:
    # Worker -> client reviews have no place in the old one-way table.
    op.execute("DELETE FROM reviews WHERE direction = 'WORKER_TO_BUYER'")
    op.drop_index("ix_reviews_subject_direction", table_name="reviews")
    op.drop_constraint("uq_reviews_job_direction", "reviews", type_="unique")
    op.create_unique_constraint("uq_reviews_job", "reviews", ["job_id"])
    for name in (
        "fk_reviews_moderated_by",
        "fk_reviews_reported_by",
        "fk_reviews_subject_id",
        "fk_reviews_author_id",
    ):
        op.drop_constraint(name, "reviews", type_="foreignkey")
    for column in (
        "moderated_at",
        "moderated_by",
        "hidden_at",
        "report_reason",
        "reported_by",
        "reported_at",
        "replied_at",
        "reply",
        "had_dispute",
        "published_at",
        "visible_after",
        "subject_id",
        "author_id",
        "direction",
    ):
        op.drop_column("reviews", column)
    # Postgres can't drop enum values; the four worker -> client tags stay
    # in reviewtagenum, unused.
