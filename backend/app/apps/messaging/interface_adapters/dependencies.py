import redis.asyncio as aioredis
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.apps.jobs.infrastructure.repositories import SqlAlchemyJobRepository
from app.apps.jobs.interface_adapters.dependencies import get_job_repository
from app.apps.messaging.domain.services import (
    ListMessagesUseCase,
    MarkMessagesReadUseCase,
    SendMessageUseCase,
)
from app.apps.messaging.infrastructure.redis_chat_broadcaster import RedisChatBroadcaster
from app.apps.messaging.infrastructure.repositories import SqlAlchemyMessageRepository
from app.core.database import get_db_session
from app.core.redis import get_redis_client
from app.core.unit_of_work import SqlAlchemyUnitOfWork, get_unit_of_work


def get_message_repository(
    db: AsyncSession = Depends(get_db_session),
) -> SqlAlchemyMessageRepository:
    return SqlAlchemyMessageRepository(db)


def get_chat_broadcaster(
    redis_client: aioredis.Redis = Depends(get_redis_client),
) -> RedisChatBroadcaster:
    return RedisChatBroadcaster(redis_client)


def get_send_message_use_case(
    messages: SqlAlchemyMessageRepository = Depends(get_message_repository),
    jobs: SqlAlchemyJobRepository = Depends(get_job_repository),
    broadcaster: RedisChatBroadcaster = Depends(get_chat_broadcaster),
    uow: SqlAlchemyUnitOfWork = Depends(get_unit_of_work),
) -> SendMessageUseCase:
    return SendMessageUseCase(messages, jobs, broadcaster, uow)


def get_list_messages_use_case(
    messages: SqlAlchemyMessageRepository = Depends(get_message_repository),
    jobs: SqlAlchemyJobRepository = Depends(get_job_repository),
) -> ListMessagesUseCase:
    return ListMessagesUseCase(messages, jobs)


def get_mark_messages_read_use_case(
    messages: SqlAlchemyMessageRepository = Depends(get_message_repository),
    jobs: SqlAlchemyJobRepository = Depends(get_job_repository),
    uow: SqlAlchemyUnitOfWork = Depends(get_unit_of_work),
) -> MarkMessagesReadUseCase:
    return MarkMessagesReadUseCase(messages, jobs, uow)
