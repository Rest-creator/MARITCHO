import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.apps.jobs.domain.entities import DisputeStatusEnum, JobStatusEnum
from app.core.database import Base
from app.shared_kernel.enums import CurrencyEnum, LedgerEntryTypeEnum, TradeEnum


class JobModel(Base):
    __tablename__ = "jobs"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    buyer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("persons.id"), nullable=False, index=True
    )
    worker_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("persons.id"), index=True
    )
    status: Mapped[JobStatusEnum] = mapped_column(Enum(JobStatusEnum), nullable=False)
    trade: Mapped[TradeEnum] = mapped_column(Enum(TradeEnum), nullable=False)
    suburb: Mapped[str] = mapped_column(String(100), ForeignKey("suburbs.name"), nullable=False)
    address: Mapped[str] = mapped_column(Text, nullable=False)
    landmark_narrative: Mapped[str | None] = mapped_column(Text)
    latitude: Mapped[Decimal | None] = mapped_column(Numeric(9, 6))
    longitude: Mapped[Decimal | None] = mapped_column(Numeric(9, 6))
    problem_description: Mapped[str | None] = mapped_column(Text)
    problem_photo_url: Mapped[str | None] = mapped_column(String(255))
    # Set once at booking (ADR-002); nullable until then. Every ledger entry
    # written afterward (BALANCE_COMMITTED, RELEASED) reuses this value.
    currency: Mapped[CurrencyEnum | None] = mapped_column(Enum(CurrencyEnum))
    labor_amount: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    materials_amount: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    quote_amount: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    __table_args__ = (
        CheckConstraint(
            '(quote_amount IS NULL AND labor_amount IS NULL AND materials_amount IS NULL)'
            ' OR (quote_amount IS NOT NULL AND labor_amount IS NOT NULL'
            ' AND materials_amount IS NOT NULL'
            ' AND quote_amount = labor_amount + materials_amount)',
            name='check_job_quote_equals_labor_plus_materials',
        ),
    )


class LedgerEntryModel(Base):
    __tablename__ = "ledger_entries"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=False, index=True
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    entry_type: Mapped[LedgerEntryTypeEnum] = mapped_column(
        Enum(LedgerEntryTypeEnum), nullable=False
    )
    currency: Mapped[CurrencyEnum] = mapped_column(
        Enum(CurrencyEnum), nullable=False, default=CurrencyEnum.USD
    )
    external_reference: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )

    __table_args__ = (
        CheckConstraint('amount > 0', name='check_amount_positive'),
    )


class DisputeModel(Base):
    __tablename__ = "disputes"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=False, index=True
    )
    raised_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("persons.id"), nullable=False, index=True
    )
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[DisputeStatusEnum] = mapped_column(Enum(DisputeStatusEnum), nullable=False)
    worker_response: Mapped[str | None] = mapped_column(Text)
    before_photo_url: Mapped[str | None] = mapped_column(String(255))
    after_photo_url: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
    responded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class RecordEntryModel(Base):
    __tablename__ = "record_entries"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("jobs.id"), unique=True, nullable=False
    )
    worker_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("persons.id"), nullable=False, index=True
    )
    what_was_done: Mapped[str] = mapped_column(Text, nullable=False)
    client_words: Mapped[str | None] = mapped_column(Text)
    before_photo_url: Mapped[str | None] = mapped_column(String(255))
    after_photo_url: Mapped[str | None] = mapped_column(String(255))
    signed_off_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
