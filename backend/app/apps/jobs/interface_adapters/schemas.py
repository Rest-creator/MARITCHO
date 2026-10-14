import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.apps.jobs.domain.entities import DisputeStatusEnum, JobStatusEnum
from app.shared_kernel.enums import (
    CurrencyEnum,
    DistanceBandEnum,
    GradeEnum,
    LedgerEntryTypeEnum,
    NeededByEnum,
    ReviewTagEnum,
    TradeEnum,
)
from app.shared_kernel.text import strip_tags


class JobRequestCreate(BaseModel):
    trade: TradeEnum
    suburb: str = Field(min_length=1, max_length=100)
    address: str = Field(min_length=1, max_length=500)
    landmark_narrative: str | None = Field(default=None, max_length=500)
    latitude: Decimal | None = Field(default=None, ge=-90, le=90)
    longitude: Decimal | None = Field(default=None, ge=-180, le=180)
    problem_description: str = Field(min_length=1, max_length=2000)
    problem_photo_url: str | None = Field(default=None, max_length=255)
    budget_amount: Decimal | None = Field(default=None, gt=0, max_digits=10, decimal_places=2)
    needed_by: NeededByEnum = NeededByEnum.FLEXIBLE

    @field_validator("suburb", "address", "problem_description")
    @classmethod
    def sanitize_text(cls, value: str) -> str:
        sanitized = strip_tags(value)
        if not sanitized:
            raise ValueError("must contain non-empty text")
        return sanitized

    @field_validator("landmark_narrative")
    @classmethod
    def sanitize_landmark_narrative(cls, value: str | None) -> str | None:
        return strip_tags(value) if value is not None else value


class JobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

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
    budget_amount: Decimal | None
    currency: CurrencyEnum | None
    labor_amount: Decimal | None
    materials_amount: Decimal | None
    quote_amount: Decimal | None
    created_at: datetime
    updated_at: datetime
    needed_by: NeededByEnum = NeededByEnum.FLEXIBLE
    worker_display_name: str | None = None


class MyJobOut(BaseModel):
    """JobOut plus the number of worker-submitted JobOffers — for the
    buyer's own job list (GET /jobs/mine)."""

    model_config = ConfigDict(from_attributes=True)

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
    budget_amount: Decimal | None
    currency: CurrencyEnum | None
    labor_amount: Decimal | None
    materials_amount: Decimal | None
    quote_amount: Decimal | None
    created_at: datetime
    updated_at: datetime
    needed_by: NeededByEnum = NeededByEnum.FLEXIBLE
    worker_display_name: str | None = None
    offer_count: int


class MyOfferOut(BaseModel):
    """A worker's own submitted JobOffer, flattened with enough job
    context (trade/suburb/status) to render in a list without a second
    fetch per row — for GET /jobs/my-offers."""

    id: uuid.UUID
    job_id: uuid.UUID
    quoted_amount: Decimal
    availability_note: str | None
    created_at: datetime
    updated_at: datetime
    job_trade: TradeEnum
    job_suburb: str
    job_status: JobStatusEnum
    needed_by: NeededByEnum = NeededByEnum.FLEXIBLE


class BookingCreate(BaseModel):
    worker_id: uuid.UUID
    deposit_amount: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    currency: CurrencyEnum = CurrencyEnum.USD


class QuoteCreate(BaseModel):
    labor_amount: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    materials_amount: Decimal = Field(ge=0, max_digits=10, decimal_places=2)


class CompletionCreate(BaseModel):
    what_was_done: str = Field(min_length=1, max_length=2000)
    client_words: str | None = Field(default=None, max_length=2000)
    before_photo_url: str | None = Field(default=None, max_length=255)
    after_photo_url: str | None = Field(default=None, max_length=255)

    @field_validator("what_was_done")
    @classmethod
    def sanitize_what_was_done(cls, value: str) -> str:
        sanitized = strip_tags(value)
        if not sanitized:
            raise ValueError("must contain non-empty text")
        return sanitized

    @field_validator("client_words")
    @classmethod
    def sanitize_client_words(cls, value: str | None) -> str | None:
        return strip_tags(value) if value is not None else value


class ReviewCreate(BaseModel):
    rating: int = Field(ge=1, le=5)
    tags: list[ReviewTagEnum] = Field(default_factory=list, max_length=3)
    comment: str | None = Field(default=None, max_length=1000)

    @field_validator("comment")
    @classmethod
    def sanitize_comment(cls, value: str | None) -> str | None:
        return strip_tags(value) if value is not None else value


class DisputeCreate(BaseModel):
    reason: str = Field(min_length=1, max_length=2000)

    @field_validator("reason")
    @classmethod
    def sanitize_reason(cls, value: str) -> str:
        sanitized = strip_tags(value)
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
        sanitized = strip_tags(value)
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
    currency: CurrencyEnum
    external_reference: str | None
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
    model_config = ConfigDict(from_attributes=True)

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
    quoted_amount: Decimal | None
    availability_note: str | None
    quoted_at: datetime | None
    display_name: str | None = None
    rating_average: Decimal | None = None
    rating_count: int = 0


class JobOfferCreate(BaseModel):
    quoted_amount: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    availability_note: str | None = Field(default=None, max_length=255)

    @field_validator("availability_note")
    @classmethod
    def sanitize_availability_note(cls, value: str | None) -> str | None:
        return strip_tags(value) if value is not None else value


class JobOfferOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    job_id: uuid.UUID
    worker_id: uuid.UUID
    quoted_amount: Decimal
    availability_note: str | None
    created_at: datetime
    updated_at: datetime
    worker_display_name: str | None = None


class OpenJobOut(BaseModel):
    """Worker-facing view of a still-open job — deliberately omits
    address/landmark_narrative/latitude/longitude/buyer_id, matching the
    existing "address hidden from workers until booking" principle."""

    model_config = ConfigDict(from_attributes=True)

    job_id: uuid.UUID
    trade: TradeEnum
    suburb: str
    budget_amount: Decimal | None
    problem_description: str | None
    created_at: datetime | None
    distance_band: DistanceBandEnum
    distance_km: float
    needed_by: NeededByEnum = NeededByEnum.FLEXIBLE
