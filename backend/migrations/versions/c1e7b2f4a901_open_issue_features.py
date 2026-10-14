"""profiles, timing, reviews, media and OTP persistence."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c1e7b2f4a901"
down_revision: Union[str, Sequence[str], None] = "6d6e6e73cc27"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    for value in ("GARDENING", "CARPENTRY", "PAINTING", "TILING", "ROOFING", "GENERAL_MAINTENANCE"):
        op.execute(sa.text(f"ALTER TYPE tradeenum ADD VALUE IF NOT EXISTS '{value}'"))
    op.add_column("persons", sa.Column("display_name", sa.String(100), nullable=True))
    op.add_column(
        "persons", sa.Column("is_available", sa.Boolean(), nullable=False, server_default=sa.true())
    )
    op.add_column(
        "persons", sa.Column("travel_km", sa.Integer(), nullable=False, server_default="50")
    )
    op.add_column("persons", sa.Column("home_suburb", sa.String(100), nullable=True))
    op.create_foreign_key("fk_persons_home_suburb", "persons", "suburbs", ["home_suburb"], ["name"])
    needed_by = sa.Enum("TODAY", "THIS_WEEK", "FLEXIBLE", name="neededbyenum", create_type=False)
    sa.Enum("TODAY", "THIS_WEEK", "FLEXIBLE", name="neededbyenum").create(bind)
    op.add_column(
        "jobs", sa.Column("needed_by", needed_by, nullable=False, server_default="FLEXIBLE")
    )
    review_tag = sa.Enum(
        "CLEAN",
        "ON_TIME",
        "PROFESSIONAL",
        "GOOD_COMMUNICATION",
        "QUALITY_WORK",
        "FAIR_PRICE",
        "RELIABLE",
        name="reviewtagenum",
        create_type=False,
    )
    sa.Enum(
        "CLEAN",
        "ON_TIME",
        "PROFESSIONAL",
        "GOOD_COMMUNICATION",
        "QUALITY_WORK",
        "FAIR_PRICE",
        "RELIABLE",
        name="reviewtagenum",
    ).create(bind)
    op.create_table(
        "reviews",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("job_id", sa.UUID(), sa.ForeignKey("jobs.id"), nullable=False),
        sa.Column("buyer_id", sa.UUID(), sa.ForeignKey("persons.id"), nullable=False),
        sa.Column("worker_id", sa.UUID(), sa.ForeignKey("persons.id"), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("tags", sa.ARRAY(review_tag), nullable=False, server_default="{}"),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("rating BETWEEN 1 AND 5", name="check_review_rating"),
        sa.UniqueConstraint("job_id", name="uq_reviews_job"),
    )
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
    op.create_table(
        "media_files",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("owner_id", sa.UUID(), sa.ForeignKey("persons.id"), nullable=False),
        sa.Column("idempotency_key", sa.String(128), nullable=False),
        sa.Column("storage_name", sa.String(255), nullable=False),
        sa.Column("content_type", sa.String(100), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("owner_id", "idempotency_key", name="uq_media_owner_idempotency"),
    )


def downgrade() -> None:
    op.drop_table("media_files")
    op.drop_index("ix_otp_requests_phone_created", table_name="otp_requests")
    op.drop_table("otp_requests")
    op.drop_table("reviews")
    op.drop_column("jobs", "needed_by")
    sa.Enum(name="reviewtagenum").drop(op.get_bind())
    sa.Enum(name="neededbyenum").drop(op.get_bind())
    op.drop_constraint("fk_persons_home_suburb", "persons", type_="foreignkey")
    for column in ("home_suburb", "travel_km", "is_available", "display_name"):
        op.drop_column("persons", column)
