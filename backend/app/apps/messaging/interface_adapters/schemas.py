import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.apps.messaging.domain.entities import MessageTypeEnum
from app.shared_kernel.text import strip_tags


class MessageCreate(BaseModel):
    message_type: MessageTypeEnum
    body: str | None = Field(default=None, max_length=2000)
    media_url: str | None = Field(default=None, max_length=255)
    duration_seconds: int | None = Field(default=None, gt=0)
    latitude: Decimal | None = Field(default=None, ge=-90, le=90)
    longitude: Decimal | None = Field(default=None, ge=-180, le=180)

    @field_validator("body")
    @classmethod
    def sanitize_body(cls, value: str | None) -> str | None:
        return strip_tags(value) if value is not None else value


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    job_id: uuid.UUID
    sender_id: uuid.UUID
    message_type: MessageTypeEnum
    body: str | None
    media_url: str | None
    duration_seconds: int | None
    latitude: Decimal | None
    longitude: Decimal | None
    created_at: datetime
    read_at: datetime | None
