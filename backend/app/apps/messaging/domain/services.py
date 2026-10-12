import uuid
from collections.abc import Sequence
from decimal import Decimal

from app.apps.jobs.domain.repositories import JobRepository
from app.apps.messaging.domain.entities import Message, MessageTypeEnum
from app.apps.messaging.domain.repositories import ChatBroadcaster, MessageRepository
from app.core.exceptions import ForbiddenError, NotFoundError, ValidationConflictError
from app.shared_kernel.enums import RoleEnum
from app.shared_kernel.unit_of_work import UnitOfWork


def _validate_message_payload(
    message_type: MessageTypeEnum,
    body: str | None,
    media_url: str | None,
    latitude: Decimal | None,
    longitude: Decimal | None,
) -> None:
    if message_type == MessageTypeEnum.TEXT and not body:
        raise ValidationConflictError("A TEXT message requires a body")
    if message_type in (MessageTypeEnum.VOICE_NOTE, MessageTypeEnum.PHOTO) and not media_url:
        raise ValidationConflictError(f"A {message_type.value} message requires media_url")
    if message_type == MessageTypeEnum.LOCATION and (latitude is None or longitude is None):
        raise ValidationConflictError("A LOCATION message requires latitude and longitude")


async def _require_job_party(
    jobs: JobRepository, job_id: uuid.UUID, user_id: uuid.UUID, user_role: RoleEnum
) -> None:
    job = await jobs.get(job_id)
    if job is None:
        raise NotFoundError("Job not found")
    is_party = user_id in (job.buyer_id, job.worker_id)
    if not is_party and user_role != RoleEnum.OPS:
        raise ForbiddenError("Not permitted to view this job's messages")


class SendMessageUseCase:
    """jobs is a foundational direct dependency here (same precedent as
    workers -> accounts) — messaging doesn't own Job, but needs it for
    the party check every message send/read requires."""

    def __init__(
        self,
        messages: MessageRepository,
        jobs: JobRepository,
        broadcaster: ChatBroadcaster,
        uow: UnitOfWork,
    ) -> None:
        self._messages = messages
        self._jobs = jobs
        self._broadcaster = broadcaster
        self._uow = uow

    async def execute(
        self,
        *,
        job_id: uuid.UUID,
        sender_id: uuid.UUID,
        sender_role: RoleEnum,
        message_type: MessageTypeEnum,
        body: str | None,
        media_url: str | None,
        duration_seconds: int | None,
        latitude: Decimal | None,
        longitude: Decimal | None,
    ) -> Message:
        await _require_job_party(self._jobs, job_id, sender_id, sender_role)
        _validate_message_payload(message_type, body, media_url, latitude, longitude)

        message = await self._messages.add(
            job_id=job_id,
            sender_id=sender_id,
            message_type=message_type,
            body=body,
            media_url=media_url,
            duration_seconds=duration_seconds,
            latitude=latitude,
            longitude=longitude,
        )
        await self._uow.commit()
        # Published after commit so subscribers only ever see durably-stored messages.
        await self._broadcaster.publish(job_id, message)
        return message


class ListMessagesUseCase:
    def __init__(self, messages: MessageRepository, jobs: JobRepository) -> None:
        self._messages = messages
        self._jobs = jobs

    async def execute(
        self,
        job_id: uuid.UUID,
        current_user_id: uuid.UUID,
        current_user_role: RoleEnum,
        *,
        limit: int,
        offset: int,
    ) -> Sequence[Message]:
        await _require_job_party(self._jobs, job_id, current_user_id, current_user_role)
        return await self._messages.list_by_job(job_id, limit=limit, offset=offset)


class MarkMessagesReadUseCase:
    def __init__(self, messages: MessageRepository, jobs: JobRepository, uow: UnitOfWork) -> None:
        self._messages = messages
        self._jobs = jobs
        self._uow = uow

    async def execute(
        self, job_id: uuid.UUID, reader_id: uuid.UUID, reader_role: RoleEnum
    ) -> None:
        await _require_job_party(self._jobs, job_id, reader_id, reader_role)
        await self._messages.mark_read(job_id, reader_id)
        await self._uow.commit()
