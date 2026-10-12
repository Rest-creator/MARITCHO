import asyncio
import uuid
from collections.abc import Sequence

import jwt
import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, status

from app.apps.accounts.domain.entities import Person
from app.apps.accounts.infrastructure.repositories import SqlAlchemyPersonRepository
from app.apps.accounts.interface_adapters.dependencies import (
    get_current_user,
    get_person_repository,
)
from app.apps.jobs.infrastructure.repositories import SqlAlchemyJobRepository
from app.apps.jobs.interface_adapters.dependencies import get_job_repository
from app.apps.messaging.domain.entities import Message
from app.apps.messaging.domain.services import (
    ListMessagesUseCase,
    MarkMessagesReadUseCase,
    SendMessageUseCase,
)
from app.apps.messaging.infrastructure.redis_chat_broadcaster import channel_name
from app.apps.messaging.interface_adapters.dependencies import (
    get_list_messages_use_case,
    get_mark_messages_read_use_case,
    get_send_message_use_case,
)
from app.apps.messaging.interface_adapters.schemas import MessageCreate, MessageOut
from app.core.pagination import Pagination, pagination_params
from app.core.redis import get_redis_client
from app.core.security import decode_access_token
from app.shared_kernel.enums import RoleEnum

router = APIRouter(prefix="/jobs", tags=["messaging"])

_WS_UNAUTHORIZED = 4401
_WS_FORBIDDEN = 4403
_WS_NOT_FOUND = 4404


@router.post(
    "/{job_id}/messages", response_model=MessageOut, status_code=status.HTTP_201_CREATED
)
async def send_message(
    job_id: uuid.UUID,
    payload: MessageCreate,
    current_user: Person = Depends(get_current_user),
    use_case: SendMessageUseCase = Depends(get_send_message_use_case),
) -> Message:
    """Send a message in this job's conversation. Restricted to the job's
    buyer or assigned worker (or OPS) — enforced inside the use case, not
    a role gate, since either role may be either party."""
    return await use_case.execute(
        job_id=job_id,
        sender_id=current_user.id,
        sender_role=current_user.role,
        message_type=payload.message_type,
        body=payload.body,
        media_url=payload.media_url,
        duration_seconds=payload.duration_seconds,
        latitude=payload.latitude,
        longitude=payload.longitude,
    )


@router.get("/{job_id}/messages", response_model=list[MessageOut])
async def list_messages(
    job_id: uuid.UUID,
    current_user: Person = Depends(get_current_user),
    pagination: Pagination = Depends(pagination_params),
    use_case: ListMessagesUseCase = Depends(get_list_messages_use_case),
) -> Sequence[Message]:
    return await use_case.execute(
        job_id,
        current_user.id,
        current_user.role,
        limit=pagination.limit,
        offset=pagination.offset,
    )


@router.post("/{job_id}/messages/read", status_code=status.HTTP_204_NO_CONTENT)
async def mark_messages_read(
    job_id: uuid.UUID,
    current_user: Person = Depends(get_current_user),
    use_case: MarkMessagesReadUseCase = Depends(get_mark_messages_read_use_case),
) -> None:
    await use_case.execute(job_id, current_user.id, current_user.role)


@router.websocket("/{job_id}/ws")
async def chat_socket(
    websocket: WebSocket,
    job_id: uuid.UUID,
    token: str,
    persons: SqlAlchemyPersonRepository = Depends(get_person_repository),
    jobs: SqlAlchemyJobRepository = Depends(get_job_repository),
    redis_client: aioredis.Redis = Depends(get_redis_client),
) -> None:
    """Receive-only from the client's perspective: sending a message
    always goes through POST /{job_id}/messages above (one validation
    path, not two). This socket exists purely to push already-stored
    messages to a connected peer in real time, via Redis pub/sub so it
    works regardless of which worker process holds the connection.

    Auth travels as a `?token=` query param (not a header) — WebSocket
    handshakes can't reliably carry a bearer Authorization header across
    all client platforms.
    """
    try:
        payload = decode_access_token(token)
        phone = payload.get("sub")
        user = await persons.get_by_phone(phone) if isinstance(phone, str) else None
    except jwt.PyJWTError:
        user = None

    if user is None:
        await websocket.close(code=_WS_UNAUTHORIZED)
        return

    job = await jobs.get(job_id)
    if job is None:
        await websocket.close(code=_WS_NOT_FOUND)
        return

    is_party = user.id in (job.buyer_id, job.worker_id)
    if not is_party and user.role != RoleEnum.OPS:
        await websocket.close(code=_WS_FORBIDDEN)
        return

    await websocket.accept()

    pubsub = redis_client.pubsub()
    await pubsub.subscribe(channel_name(job_id))

    async def forward_messages() -> None:
        async for item in pubsub.listen():
            if item["type"] == "message":
                await websocket.send_text(item["data"])

    async def wait_for_disconnect() -> None:
        try:
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            return

    forward_task = asyncio.create_task(forward_messages())
    disconnect_task = asyncio.create_task(wait_for_disconnect())

    try:
        await asyncio.wait(
            [forward_task, disconnect_task], return_when=asyncio.FIRST_COMPLETED
        )
    finally:
        forward_task.cancel()
        disconnect_task.cancel()
        await pubsub.unsubscribe(channel_name(job_id))
        await pubsub.aclose()  # type: ignore[no-untyped-call]  # redis-py stub gap on PubSub.aclose
