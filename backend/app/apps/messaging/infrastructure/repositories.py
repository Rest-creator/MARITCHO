import uuid
from collections.abc import Sequence
from datetime import datetime
from decimal import Decimal

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.apps.messaging.domain.entities import Message, MessageTypeEnum
from app.apps.messaging.domain.repositories import MessageRepository
from app.apps.messaging.infrastructure.models import MessageModel


def _message_to_entity(model: MessageModel) -> Message:
    return Message(
        id=model.id,
        job_id=model.job_id,
        sender_id=model.sender_id,
        message_type=model.message_type,
        body=model.body,
        media_url=model.media_url,
        duration_seconds=model.duration_seconds,
        latitude=model.latitude,
        longitude=model.longitude,
        created_at=model.created_at,
        read_at=model.read_at,
    )


class SqlAlchemyMessageRepository(MessageRepository):
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

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
        model = MessageModel(
            job_id=job_id,
            sender_id=sender_id,
            message_type=message_type,
            body=body,
            media_url=media_url,
            duration_seconds=duration_seconds,
            latitude=latitude,
            longitude=longitude,
        )
        self._db.add(model)
        await self._db.flush()
        return _message_to_entity(model)

    async def list_by_job(
        self, job_id: uuid.UUID, *, limit: int, offset: int
    ) -> Sequence[Message]:
        result = await self._db.execute(
            select(MessageModel)
            .where(MessageModel.job_id == job_id)
            .order_by(MessageModel.created_at)
            .limit(limit)
            .offset(offset)
        )
        return [_message_to_entity(model) for model in result.scalars().all()]

    async def mark_read(self, job_id: uuid.UUID, reader_id: uuid.UUID) -> None:
        await self._db.execute(
            update(MessageModel)
            .where(
                MessageModel.job_id == job_id,
                MessageModel.sender_id != reader_id,
                MessageModel.read_at.is_(None),
            )
            .values(read_at=datetime.utcnow())
        )
        await self._db.flush()
