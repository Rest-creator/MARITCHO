import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.apps.crews.domain.entities import CrewOrderStatusEnum
from app.shared_kernel.enums import CurrencyEnum, DistanceBandEnum, LedgerEntryTypeEnum, TradeEnum
from app.shared_kernel.text import strip_tags


class CrewCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)

    @field_validator("name")
    @classmethod
    def sanitize_name(cls, value: str) -> str:
        sanitized = strip_tags(value)
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
    landmark_narrative: str | None = Field(default=None, max_length=500)
    latitude: Decimal | None = Field(default=None, ge=-90, le=90)
    longitude: Decimal | None = Field(default=None, ge=-180, le=180)
    workers_needed: int = Field(gt=0, le=1000)
    problem_description: str | None = Field(default=None, max_length=2000)

    @field_validator("suburb", "address")
    @classmethod
    def sanitize_text(cls, value: str) -> str:
        sanitized = strip_tags(value)
        if not sanitized:
            raise ValueError("must contain non-empty text")
        return sanitized

    @field_validator("problem_description", "landmark_narrative")
    @classmethod
    def sanitize_description(cls, value: str | None) -> str | None:
        return strip_tags(value) if value is not None else value


class CrewOrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    buyer_id: uuid.UUID
    crew_id: uuid.UUID | None
    status: CrewOrderStatusEnum
    trade: TradeEnum
    suburb: str
    address: str
    landmark_narrative: str | None
    latitude: Decimal | None
    longitude: Decimal | None
    workers_needed: int
    problem_description: str | None
    currency: CurrencyEnum | None
    labor_amount: Decimal | None
    materials_amount: Decimal | None
    quote_amount: Decimal | None
    completion_note: str | None
    created_at: datetime
    updated_at: datetime


class CrewBookingCreate(BaseModel):
    crew_id: uuid.UUID
    deposit_amount: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    currency: CurrencyEnum = CurrencyEnum.USD


class CrewOrderQuoteCreate(BaseModel):
    labor_amount: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    materials_amount: Decimal = Field(ge=0, max_digits=10, decimal_places=2)


class CrewOrderCompletionCreate(BaseModel):
    what_was_done: str = Field(min_length=1, max_length=2000)

    @field_validator("what_was_done")
    @classmethod
    def sanitize_what_was_done(cls, value: str) -> str:
        sanitized = strip_tags(value)
        if not sanitized:
            raise ValueError("must contain non-empty text")
        return sanitized


class CrewOrderLedgerEntryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    crew_order_id: uuid.UUID
    amount: Decimal
    entry_type: LedgerEntryTypeEnum
    currency: CurrencyEnum
    external_reference: str | None
    created_at: datetime


class CrewMatchCandidateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    crew_id: uuid.UUID
    crew_name: str | None
    lead_id: uuid.UUID
    qualifying_members: int
    total_members: int
    distance_band: DistanceBandEnum
    distance_km: float
    reason: str
