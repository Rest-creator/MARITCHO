import enum
import uuid
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


class MessageTypeEnum(str, enum.Enum):
    TEXT = "TEXT"
    VOICE_NOTE = "VOICE_NOTE"
    PHOTO = "PHOTO"
    LOCATION = "LOCATION"


@dataclass
class Message:
    id: uuid.UUID
    job_id: uuid.UUID
    sender_id: uuid.UUID
    message_type: MessageTypeEnum
    body: str | None
    media_url: str | None
    duration_seconds: int | None
    latitude: Decimal | None
    longitude: Decimal | None
    created_at: datetime | None = None
    read_at: datetime | None = None
