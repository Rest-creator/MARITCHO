import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Numeric, Integer, ForeignKey, DateTime, Enum, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base
import enum

class RoleEnum(str, enum.Enum):
    BUYER = "BUYER"
    WORKER = "WORKER"
    OPS = "OPS"
    AGGREGATOR = "AGGREGATOR"

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

class Person(Base):
    __tablename__ = "persons"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phone = Column(String(20), unique=True, nullable=False)
    role = Column(Enum(RoleEnum), nullable=False)
    next_of_kin_phone = Column(String(20))
    guarantor_id = Column(UUID(as_uuid=True), ForeignKey("persons.id"))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

class Skill(Base):
    __tablename__ = "skills"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    worker_id = Column(UUID(as_uuid=True), ForeignKey("persons.id", ondelete="CASCADE"), nullable=False)
    trade = Column(String(50), nullable=False)
    grade = Column(String(50))
    proof_url = Column(String(255))
    
    # Needs UniqueConstraint('worker_id', 'trade') in args

class ServiceArea(Base):
    __tablename__ = "service_areas"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    worker_id = Column(UUID(as_uuid=True), ForeignKey("persons.id", ondelete="CASCADE"), nullable=False)
    suburb = Column(String(100), nullable=False)
    travel_means = Column(String(50))

class Standing(Base):
    __tablename__ = "standings"
    worker_id = Column(UUID(as_uuid=True), ForeignKey("persons.id", ondelete="CASCADE"), primary_key=True)
    grade = Column(String(50), default="REGISTERED")
    on_time_rate = Column(Numeric(5, 2), default=100.00)
    dispute_rate = Column(Numeric(5, 2), default=0.00)
    fill_rate = Column(Numeric(5, 2), default=0.00)
    jobs_completed = Column(Integer, default=0)

class Job(Base):
    __tablename__ = "jobs"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    buyer_id = Column(UUID(as_uuid=True), ForeignKey("persons.id"), nullable=False)
    worker_id = Column(UUID(as_uuid=True), ForeignKey("persons.id"))
    status = Column(Enum(JobStatusEnum), nullable=False)
    suburb = Column(String(100), nullable=False)
    problem_description = Column(Text)
    problem_photo_url = Column(String(255))
    quote_amount = Column(Numeric(10, 2))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

class LedgerEntry(Base):
    __tablename__ = "ledger_entries"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    entry_type = Column(Enum(LedgerEntryTypeEnum), nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    __table_args__ = (
        CheckConstraint('amount > 0', name='check_amount_positive'),
    )

class RecordEntry(Base):
    __tablename__ = "record_entries"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"), unique=True, nullable=False)
    worker_id = Column(UUID(as_uuid=True), ForeignKey("persons.id"), nullable=False)
    what_was_done = Column(Text, nullable=False)
    client_words = Column(Text)
    before_photo_url = Column(String(255))
    after_photo_url = Column(String(255))
    signed_off_at = Column(DateTime(timezone=True), nullable=False)
