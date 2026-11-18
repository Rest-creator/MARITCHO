import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.apps.messaging.domain.entities import MessageTypeEnum
from app.core.database import Base
from app.shared_kernel.clock import utcnow


class MessageModel(Base):
    __tablename__ = "messages"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=False, index=True
    )
    sender_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("persons.id"), nullable=False, index=True
    )
    message_type: Mapped[MessageTypeEnum] = mapped_column(Enum(MessageTypeEnum), nullable=False)
    body: Mapped[str | None] = mapped_column(Text)
    # Client-supplied URL string, same honesty note as problem_photo_url /
    # before_photo_url / after_photo_url elsewhere — no upload storage
    # exists anywhere in this backend.
    media_url: Mapped[str | None] = mapped_column(String(255))
    duration_seconds: Mapped[int | None] = mapped_column(Integer)
    latitude: Mapped[Decimal | None] = mapped_column(Numeric(9, 6))
    longitude: Mapped[Decimal | None] = mapped_column(Numeric(9, 6))
    # Aware UTC: a naive utcnow() went straight into the POST response and the
    # WebSocket payload without an offset, and browsers showed it 2h early.
    created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=utcnow)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
