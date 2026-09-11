import enum
import re
import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models import (
    CrewOrderStatusEnum,
    DisputeStatusEnum,
    GradeEnum,
    JobStatusEnum,
    LedgerEntryTypeEnum,
    TradeEnum,
)


class DistanceBandEnum(str, enum.Enum):
    SAME_SUBURB = "SAME_SUBURB"
    NEARBY = "NEARBY"
    MODERATE = "MODERATE"
    FAR = "FAR"

_TAG_RE = re.compile(r"<[^>]*>")


def _strip_tags(value: str) -> str:
    return _TAG_RE.sub("", value).strip()


class JobRequestCreate(BaseModel):
    trade: TradeEnum
    suburb: str = Field(min_length=1, max_length=100)
    address: str = Field(min_length=1, max_length=500)
    problem_description: str = Field(min_length=1, max_length=2000)
    problem_photo_url: str | None = Field(default=None, max_length=255)

    @field_validator("suburb", "address", "problem_description")
    @classmethod
    def sanitize_text(cls, value: str) -> str:
        sanitized = _strip_tags(value)
        if not sanitized:
            raise ValueError("must contain non-empty text")
        return sanitized


class JobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    buyer_id: uuid.UUID
    worker_id: uuid.UUID | None
    status: JobStatusEnum
    trade: TradeEnum
    suburb: str
    address: str
    problem_description: str | None
    problem_photo_url: str | None
    quote_amount: Decimal | None
    created_at: datetime
    updated_at: datetime


class BookingCreate(BaseModel):
    worker_id: uuid.UUID
    deposit_amount: Decimal = Field(gt=0, max_digits=10, decimal_places=2)


class QuoteCreate(BaseModel):
    quote_amount: Decimal = Field(gt=0, max_digits=10, decimal_places=2)


class CompletionCreate(BaseModel):
    what_was_done: str = Field(min_length=1, max_length=2000)
    client_words: str | None = Field(default=None, max_length=2000)
    before_photo_url: str | None = Field(default=None, max_length=255)
    after_photo_url: str | None = Field(default=None, max_length=255)

    @field_validator("what_was_done")
    @classmethod
    def sanitize_what_was_done(cls, value: str) -> str:
        sanitized = _strip_tags(value)
        if not sanitized:
            raise ValueError("must contain non-empty text")
        return sanitized

    @field_validator("client_words")
    @classmethod
    def sanitize_client_words(cls, value: str | None) -> str | None:
        return _strip_tags(value) if value is not None else value


class DisputeCreate(BaseModel):
    reason: str = Field(min_length=1, max_length=2000)

    @field_validator("reason")
    @classmethod
    def sanitize_reason(cls, value: str) -> str:
        sanitized = _strip_tags(value)
        if not sanitized:
            raise ValueError("must contain non-empty text")
        return sanitized


class DisputeResponseCreate(BaseModel):
    response: str = Field(min_length=1, max_length=2000)
    before_photo_url: str | None = Field(default=None, max_length=255)
    after_photo_url: str | None = Field(default=None, max_length=255)

    @field_validator("response")
    @classmethod
    def sanitize_response(cls, value: str) -> str:
        sanitized = _strip_tags(value)
        if not sanitized:
            raise ValueError("must contain non-empty text")
        return sanitized


class DisputeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    job_id: uuid.UUID
    raised_by_id: uuid.UUID
    reason: str
    status: DisputeStatusEnum
    worker_response: str | None
    before_photo_url: str | None
    after_photo_url: str | None
    created_at: datetime
    responded_at: datetime | None


class LedgerEntryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    job_id: uuid.UUID
    amount: Decimal
    entry_type: LedgerEntryTypeEnum
    created_at: datetime


class RecordEntryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    job_id: uuid.UUID
    worker_id: uuid.UUID
    what_was_done: str
    client_words: str | None
    before_photo_url: str | None
    after_photo_url: str | None
    signed_off_at: datetime


class MatchCandidateOut(BaseModel):
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


class SkillCreate(BaseModel):
    trade: TradeEnum
    proof_url: str | None = Field(default=None, max_length=255)


class SkillOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    worker_id: uuid.UUID
    trade: TradeEnum
    grade: GradeEnum | None
    proof_url: str | None


class ServiceAreaCreate(BaseModel):
    suburb: str = Field(min_length=1, max_length=100)
    travel_means: str | None = Field(default=None, max_length=50)


class ServiceAreaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    worker_id: uuid.UUID
    suburb: str
    travel_means: str | None


class StandingOut(BaseModel):
    worker_id: uuid.UUID
    grade: GradeEnum
    on_time_rate: Decimal
    dispute_rate: Decimal
    fill_rate: Decimal
    jobs_completed: int
    is_frozen: bool


class SuburbOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    latitude: Decimal
    longitude: Decimal


class CrewCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)

    @field_validator("name")
    @classmethod
    def sanitize_name(cls, value: str) -> str:
        sanitized = _strip_tags(value)
        if not sanitized:
            raise ValueError("must contain non-empty text")
        return sanitized


class CrewMemberAdd(BaseModel):
    worker_id: uuid.UUID


class CrewOut(BaseModel):
    id: uuid.UUID
    lead_id: uuid.UUID
    name: str | None
    member_ids: list[uuid.UUID]


class CrewOrderCreate(BaseModel):
    trade: TradeEnum
    suburb: str = Field(min_length=1, max_length=100)
    address: str = Field(min_length=1, max_length=500)
    workers_needed: int = Field(gt=0, le=1000)
    problem_description: str | None = Field(default=None, max_length=2000)

    @field_validator("suburb", "address")
    @classmethod
    def sanitize_text(cls, value: str) -> str:
        sanitized = _strip_tags(value)
        if not sanitized:
            raise ValueError("must contain non-empty text")
        return sanitized

    @field_validator("problem_description")
    @classmethod
    def sanitize_description(cls, value: str | None) -> str | None:
        return _strip_tags(value) if value is not None else value


class CrewOrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    buyer_id: uuid.UUID
    crew_id: uuid.UUID | None
    status: CrewOrderStatusEnum
    trade: TradeEnum
    suburb: str
    address: str
    workers_needed: int
    problem_description: str | None
    quote_amount: Decimal | None
    completion_note: str | None
    created_at: datetime
    updated_at: datetime


class CrewBookingCreate(BaseModel):
    crew_id: uuid.UUID
    deposit_amount: Decimal = Field(gt=0, max_digits=10, decimal_places=2)


class CrewOrderQuoteCreate(BaseModel):
    quote_amount: Decimal = Field(gt=0, max_digits=10, decimal_places=2)


class CrewOrderCompletionCreate(BaseModel):
    what_was_done: str = Field(min_length=1, max_length=2000)

    @field_validator("what_was_done")
    @classmethod
    def sanitize_what_was_done(cls, value: str) -> str:
        sanitized = _strip_tags(value)
        if not sanitized:
            raise ValueError("must contain non-empty text")
        return sanitized


class CrewOrderLedgerEntryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    crew_order_id: uuid.UUID
    amount: Decimal
    entry_type: LedgerEntryTypeEnum
    created_at: datetime


class CrewMatchCandidateOut(BaseModel):
    crew_id: uuid.UUID
    crew_name: str | None
    lead_id: uuid.UUID
    qualifying_members: int
    total_members: int
    distance_band: DistanceBandEnum
    distance_km: float
    reason: str
