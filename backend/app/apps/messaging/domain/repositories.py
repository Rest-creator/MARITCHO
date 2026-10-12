import uuid
from abc import ABC, abstractmethod
from collections.abc import Sequence
from decimal import Decimal

from app.apps.messaging.domain.entities import Message, MessageTypeEnum


class MessageRepository(ABC):
    @abstractmethod
    async def add(
        self,
        *,
        job_id: uuid.UUID,
        sender_id: uuid.UUID,
        message_type: MessageTypeEnum,
        body: str | None,
        media_url: str | None,
        duration_seconds: int | None,
        latitude: Decimal | None,
        longitude: Decimal | None,
    ) -> Message:
        """Flushes (populating id/timestamps). Does not commit."""

    @abstractmethod
    async def list_by_job(
        self, job_id: uuid.UUID, *, limit: int, offset: int
    ) -> Sequence[Message]:
        """Oldest-first, same ascending convention as LedgerEntryRepository/
        DisputeRepository's list_by_job."""

    @abstractmethod
    async def mark_read(self, job_id: uuid.UUID, reader_id: uuid.UUID) -> None:
        """Bulk-marks every unread message in this job not sent by
        reader_id as read. Flushes only — does not commit."""


class ChatBroadcaster(ABC):
    """Publishes a newly-sent message for real-time fan-out to any
    connected WebSocket clients for this job. Owned by this app's
    infrastructure (RedisChatBroadcaster) — kept as a port so the domain
    layer never imports redis.asyncio directly."""

    @abstractmethod
    async def publish(self, job_id: uuid.UUID, message: Message) -> None: ...
