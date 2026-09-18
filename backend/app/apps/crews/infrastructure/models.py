import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.apps.crews.domain.entities import CrewOrderStatusEnum
from app.core.database import Base
from app.shared_kernel.enums import CurrencyEnum, LedgerEntryTypeEnum, TradeEnum


class CrewModel(Base):
    __tablename__ = "crews"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lead_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("persons.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    name: Mapped[str | None] = mapped_column(String(100))


class CrewMemberModel(Base):
    __tablename__ = "crew_members"
    crew_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("crews.id", ondelete="CASCADE"), primary_key=True
    )
    worker_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("persons.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    )


class CrewOrderModel(Base):
    __tablename__ = "crew_orders"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    buyer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("persons.id"), nullable=False, index=True
    )
    crew_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("crews.id"), index=True
    )
    status: Mapped[CrewOrderStatusEnum] = mapped_column(Enum(CrewOrderStatusEnum), nullable=False)
    trade: Mapped[TradeEnum] = mapped_column(Enum(TradeEnum), nullable=False)
    suburb: Mapped[str] = mapped_column(String(100), ForeignKey("suburbs.name"), nullable=False)
    address: Mapped[str] = mapped_column(Text, nullable=False)
    landmark_narrative: Mapped[str | None] = mapped_column(Text)
    latitude: Mapped[Decimal | None] = mapped_column(Numeric(9, 6))
    longitude: Mapped[Decimal | None] = mapped_column(Numeric(9, 6))
    workers_needed: Mapped[int] = mapped_column(Integer, nullable=False)
    problem_description: Mapped[str | None] = mapped_column(Text)
    # Set once at booking (ADR-002); nullable until then.
    currency: Mapped[CurrencyEnum | None] = mapped_column(Enum(CurrencyEnum))
    labor_amount: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    materials_amount: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    quote_amount: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    completion_note: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    __table_args__ = (
        CheckConstraint('workers_needed > 0', name='check_workers_needed_positive'),
        CheckConstraint(
            '(quote_amount IS NULL AND labor_amount IS NULL AND materials_amount IS NULL)'
            ' OR (quote_amount IS NOT NULL AND labor_amount IS NOT NULL'
            ' AND materials_amount IS NOT NULL'
            ' AND quote_amount = labor_amount + materials_amount)',
            name='check_crew_order_quote_equals_labor_plus_materials',
        ),
    )


class CrewOrderLedgerEntryModel(Base):
    __tablename__ = "crew_order_ledger_entries"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    crew_order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("crew_orders.id"), nullable=False, index=True
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
        CheckConstraint('amount > 0', name='check_crew_order_amount_positive'),
    )
