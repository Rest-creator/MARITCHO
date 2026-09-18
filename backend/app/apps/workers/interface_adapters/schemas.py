import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.shared_kernel.enums import GradeEnum, TradeEnum
from app.shared_kernel.text import strip_tags


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


class IdPhotoSubmit(BaseModel):
    id_photo_url: str = Field(min_length=1, max_length=255)


class ReferenceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    phone: str = Field(min_length=1, max_length=20)

    @field_validator("name")
    @classmethod
    def sanitize_name(cls, value: str) -> str:
        sanitized = strip_tags(value)
        if not sanitized:
            raise ValueError("must contain non-empty text")
        return sanitized


class ReferenceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    worker_id: uuid.UUID
    name: str
    phone: str
    created_at: datetime


class VouchCreate(BaseModel):
    worker_id: uuid.UUID


class VouchOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    worker_id: uuid.UUID
    voucher_id: uuid.UUID
    created_at: datetime


class WorkerVettingOut(BaseModel):
    worker_id: uuid.UUID
    id_photo_url: str | None
    id_submitted_at: datetime | None
    reference_count: int
    vouch_count: int
    grade: GradeEnum
