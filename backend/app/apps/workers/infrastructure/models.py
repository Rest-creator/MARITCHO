import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.shared_kernel.enums import GradeEnum, TradeEnum


class SkillModel(Base):
    __tablename__ = "skills"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    worker_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("persons.id", ondelete="CASCADE"), nullable=False
    )
    trade: Mapped[TradeEnum] = mapped_column(Enum(TradeEnum), nullable=False)
    grade: Mapped[GradeEnum | None] = mapped_column(Enum(GradeEnum))
    proof_url: Mapped[str | None] = mapped_column(String(255))

    __table_args__ = (
        UniqueConstraint('worker_id', 'trade', name='uq_skills_worker_trade'),
    )


class ServiceAreaModel(Base):
    __tablename__ = "service_areas"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    worker_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("persons.id", ondelete="CASCADE"), nullable=False
    )
    suburb: Mapped[str] = mapped_column(String(100), ForeignKey("suburbs.name"), nullable=False)
    travel_means: Mapped[str | None] = mapped_column(String(50))

    __table_args__ = (
        UniqueConstraint('worker_id', 'suburb', name='uq_service_areas_worker_suburb'),
    )


class StandingModel(Base):
    __tablename__ = "standings"
    worker_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("persons.id", ondelete="CASCADE"), primary_key=True
    )
    grade: Mapped[GradeEnum | None] = mapped_column(Enum(GradeEnum), default=GradeEnum.REGISTERED)
    on_time_rate: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), default=100.00)
    dispute_rate: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), default=0.00)
    fill_rate: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), default=0.00)
    jobs_completed: Mapped[int | None] = mapped_column(Integer, default=0)


class WorkerVettingModel(Base):
    """Progressive vetting evidence (ADR-005): a photographed national ID.

    One row per worker. References and vouches live in their own tables
    since they're one-to-many; this table holds the single ID-photo
    checkpoint that gates the REGISTERED -> IDENTIFIED promotion.
    """
    __tablename__ = "worker_vetting"
    worker_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("persons.id", ondelete="CASCADE"), primary_key=True
    )
    id_photo_url: Mapped[str | None] = mapped_column(String(255))
    id_submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class WorkerReferenceModel(Base):
    """A contactable reference submitted by a worker (ADR-005: IDENTIFIED -> APPRENTICE)."""
    __tablename__ = "worker_references"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    worker_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("persons.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )


class WorkerVouchModel(Base):
    """A higher-tier ('master') worker vouching for another.

    ADR-005: gates APPRENTICE -> JOURNEYMAN/EXPERT.

    `worker_id` is the worker being vouched for; `voucher_id` is the
    vouching worker. The voucher's grade is checked at write time
    (JOURNEYMAN or EXPERT required) in the use case; there is no stored
    snapshot of the voucher's grade at vouch time —
    RecomputeGradeUseCase always re-checks the voucher's *current* grade.
    """
    __tablename__ = "worker_vouches"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    worker_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("persons.id", ondelete="CASCADE"), nullable=False, index=True
    )
    voucher_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("persons.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )

    __table_args__ = (
        UniqueConstraint('worker_id', 'voucher_id', name='uq_worker_vouches_worker_voucher'),
        CheckConstraint('worker_id != voucher_id', name='check_worker_vouches_no_self_vouch'),
    )
