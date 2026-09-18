import enum
import uuid
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from app.shared_kernel.enums import (
    CurrencyEnum,
    DistanceBandEnum,
    GradeEnum,
    LedgerEntryTypeEnum,
    TradeEnum,
)


class JobStatusEnum(str, enum.Enum):
    REQUESTED = "REQUESTED"
    MATCHED = "MATCHED"
    BOOKED = "BOOKED"
    IN_PROGRESS = "IN_PROGRESS"
    DISPUTED = "DISPUTED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class DisputeStatusEnum(str, enum.Enum):
    OPEN = "OPEN"
    RESOLVED_RETURN_VISIT = "RESOLVED_RETURN_VISIT"


# A worker already tied to one of these job states is not available for a new match.
JOB_BUSY_STATUSES = (
    JobStatusEnum.MATCHED,
    JobStatusEnum.BOOKED,
    JobStatusEnum.IN_PROGRESS,
    JobStatusEnum.DISPUTED,
)


@dataclass
class Job:
    id: uuid.UUID
    buyer_id: uuid.UUID
    worker_id: uuid.UUID | None
    status: JobStatusEnum
    trade: TradeEnum
    suburb: str
    address: str
    landmark_narrative: str | None
    latitude: Decimal | None
    longitude: Decimal | None
    problem_description: str | None
    problem_photo_url: str | None
    currency: CurrencyEnum | None
    labor_amount: Decimal | None
    materials_amount: Decimal | None
    quote_amount: Decimal | None
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass
class LedgerEntry:
    id: uuid.UUID
    job_id: uuid.UUID
    amount: Decimal
    entry_type: LedgerEntryTypeEnum
    currency: CurrencyEnum
    external_reference: str | None = None
    created_at: datetime | None = None


@dataclass
class Dispute:
    id: uuid.UUID
    job_id: uuid.UUID
    raised_by_id: uuid.UUID
    reason: str
    status: DisputeStatusEnum
    worker_response: str | None = None
    before_photo_url: str | None = None
    after_photo_url: str | None = None
    created_at: datetime | None = None
    responded_at: datetime | None = None


@dataclass
class RecordEntry:
    id: uuid.UUID
    job_id: uuid.UUID
    worker_id: uuid.UUID
    what_was_done: str
    client_words: str | None
    before_photo_url: str | None
    after_photo_url: str | None
    signed_off_at: datetime


@dataclass
class MatchCandidate:
    """Domain-level result of the matching engine — mapped to
    interface_adapters.schemas.MatchCandidateOut by the router."""

    worker_id: uuid.UUID
    suburb: str
    travel_means: str | None
    distance_band: DistanceBandEnum
    distance_km: float
    grade: GradeEnum
    on_time_rate: Decimal
    dispute_rate: Decimal
    fill_rate: Decimal
    jobs_completed: int
    reason: str
