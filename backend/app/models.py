import enum
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
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class RoleEnum(str, enum.Enum):
    BUYER = "BUYER"
    WORKER = "WORKER"
    OPS = "OPS"
    AGGREGATOR = "AGGREGATOR"

class TradeEnum(str, enum.Enum):
    PLUMBING = "PLUMBING"
    ELECTRICAL = "ELECTRICAL"
    SOLAR = "SOLAR"
    WELDING = "WELDING"
    BUILDING = "BUILDING"
    APPLIANCE_REPAIR = "APPLIANCE_REPAIR"

class JobStatusEnum(str, enum.Enum):
    REQUESTED = "REQUESTED"
    MATCHED = "MATCHED"
    BOOKED = "BOOKED"
    IN_PROGRESS = "IN_PROGRESS"
    DISPUTED = "DISPUTED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

class LedgerEntryTypeEnum(str, enum.Enum):
    DEPOSIT_HELD = "DEPOSIT_HELD"
    BALANCE_COMMITTED = "BALANCE_COMMITTED"
    RELEASED = "RELEASED"
    REFUNDED = "REFUNDED"

class DisputeStatusEnum(str, enum.Enum):
    OPEN = "OPEN"
    RESOLVED_RETURN_VISIT = "RESOLVED_RETURN_VISIT"

class CrewOrderStatusEnum(str, enum.Enum):
    REQUESTED = "REQUESTED"
    MATCHED = "MATCHED"
    BOOKED = "BOOKED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

class GradeEnum(str, enum.Enum):
    REGISTERED = "REGISTERED"
    IDENTIFIED = "IDENTIFIED"
    APPRENTICE = "APPRENTICE"
    JOURNEYMAN = "JOURNEYMAN"
    EXPERT = "EXPERT"

class Suburb(Base):
    __tablename__ = "suburbs"
    name: Mapped[str] = mapped_column(String(100), primary_key=True)
    latitude: Mapped[Decimal] = mapped_column(Numeric(9, 6), nullable=False)
    longitude: Mapped[Decimal] = mapped_column(Numeric(9, 6), nullable=False)

class Person(Base):
    __tablename__ = "persons"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phone: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    role: Mapped[RoleEnum] = mapped_column(Enum(RoleEnum), nullable=False)
    next_of_kin_phone: Mapped[str | None] = mapped_column(String(20))
    guarantor_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("persons.id"), index=True
    )
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )

class Skill(Base):
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

class ServiceArea(Base):
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

class Crew(Base):
    __tablename__ = "crews"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lead_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("persons.id", ondelete="CASCADE"),
        unique=True, nullable=False
    )
    name: Mapped[str | None] = mapped_column(String(100))

class CrewMember(Base):
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

class CrewOrder(Base):
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
    workers_needed: Mapped[int] = mapped_column(Integer, nullable=False)
    problem_description: Mapped[str | None] = mapped_column(Text)
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
    )

class CrewOrderLedgerEntry(Base):
    __tablename__ = "crew_order_ledger_entries"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    crew_order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("crew_orders.id"), nullable=False, index=True
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    entry_type: Mapped[LedgerEntryTypeEnum] = mapped_column(
        Enum(LedgerEntryTypeEnum), nullable=False
    )
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )

    __table_args__ = (
        CheckConstraint('amount > 0', name='check_crew_order_amount_positive'),
    )

class Standing(Base):
    __tablename__ = "standings"
    worker_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("persons.id", ondelete="CASCADE"), primary_key=True
    )
    grade: Mapped[GradeEnum | None] = mapped_column(Enum(GradeEnum), default=GradeEnum.REGISTERED)
    on_time_rate: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), default=100.00)
    dispute_rate: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), default=0.00)
    fill_rate: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), default=0.00)
    jobs_completed: Mapped[int | None] = mapped_column(Integer, default=0)

class Job(Base):
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
    problem_description: Mapped[str | None] = mapped_column(Text)
    problem_photo_url: Mapped[str | None] = mapped_column(String(255))
    quote_amount: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

class LedgerEntry(Base):
    __tablename__ = "ledger_entries"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=False, index=True
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    entry_type: Mapped[LedgerEntryTypeEnum] = mapped_column(
        Enum(LedgerEntryTypeEnum), nullable=False
    )
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )

    __table_args__ = (
        CheckConstraint('amount > 0', name='check_amount_positive'),
    )

class Dispute(Base):
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

class RecordEntry(Base):
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
