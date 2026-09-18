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
    currency: CurrencyEnum | None
    labor_amount: Decimal | None
    materials_amount: Decimal | None
    quote_amount: Decimal | None
    created_at: datetime
    updated_at: datetime


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
