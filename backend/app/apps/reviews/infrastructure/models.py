import uuid
from datetime import datetime

from sqlalchemy import (
    ARRAY,
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    and_,
    or_,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql.elements import ColumnElement

from app.core.database import Base
from app.shared_kernel.enums import ReviewDirectionEnum, ReviewTagEnum


class ReviewModel(Base):
    """One side's review of the other on a completed job (ADR-011).

    `buyer_id`/`worker_id` are the job's two parties whatever the direction;
    `author_id`/`subject_id` say who wrote it and who it is about.
    """

    __tablename__ = "reviews"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=False
    )
    buyer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("persons.id"), nullable=False
    )
    worker_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("persons.id"), nullable=False
    )
    direction: Mapped[ReviewDirectionEnum] = mapped_column(
        Enum(ReviewDirectionEnum, native_enum=False, length=20),
        nullable=False,
        default=ReviewDirectionEnum.BUYER_TO_WORKER,
        server_default=ReviewDirectionEnum.BUYER_TO_WORKER.value,
    )
    author_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("persons.id"), nullable=False
    )
    subject_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("persons.id"), nullable=False
    )
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    tags: Mapped[list[ReviewTagEnum]] = mapped_column(
        ARRAY(Enum(ReviewTagEnum, name="reviewtagenum")), nullable=False, default=list
    )
    comment: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    # Double-blind: shown once published (both sides reviewed) or after this.
    visible_after: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    had_dispute: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    reply: Mapped[str | None] = mapped_column(Text)
    replied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reported_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reported_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("persons.id", ondelete="SET NULL")
    )
    report_reason: Mapped[str | None] = mapped_column(String(255))
    hidden_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    moderated_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("persons.id", ondelete="SET NULL")
    )
    moderated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = (
        CheckConstraint("rating BETWEEN 1 AND 5", name="check_review_rating"),
        UniqueConstraint("job_id", "direction", name="uq_reviews_job_direction"),
        Index("ix_reviews_subject_direction", "subject_id", "direction"),
    )


def visible_review_clause(now: datetime) -> ColumnElement[bool]:
    """SQL twin of Review.is_visible: not removed, and published or past its window."""
    return and_(
        ReviewModel.hidden_at.is_(None),
        or_(ReviewModel.published_at.is_not(None), ReviewModel.visible_after <= now),
    )
