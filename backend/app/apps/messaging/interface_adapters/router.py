import asyncio
import uuid
from collections.abc import Sequence

import jwt
import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, status
from opentelemetry import trace
from sqlalchemy.ext.asyncio import AsyncSession

from app.apps.accounts.domain.entities import Person
from app.apps.accounts.infrastructure.repositories import SqlAlchemyPersonRepository
from app.apps.accounts.interface_adapters.dependencies import get_current_user
from app.apps.jobs.domain.entities import JobStatusEnum
from app.apps.jobs.infrastructure.repositories import (
    SqlAlchemyJobOfferRepository,
    SqlAlchemyJobRepository,
)
from app.apps.messaging.domain.entities import Message
from app.apps.messaging.domain.services import (
    ListMessagesUseCase,
    MarkMessagesReadUseCase,
    SendMessageUseCase,
)
from app.apps.messaging.infrastructure.redis_chat_broadcaster import channel_name
from app.apps.messaging.infrastructure.unread import ConversationUnread, unread_summary
from app.apps.messaging.interface_adapters.dependencies import (
    get_list_messages_use_case,
    get_mark_messages_read_use_case,
    get_send_message_use_case,
)
from app.apps.messaging.interface_adapters.schemas import (
    ConversationUnreadOut,
    MessageCreate,
    MessageOut,
)
from app.core.database import AsyncSessionLocal, get_db_session
from app.core.pagination import Pagination, pagination_params
from app.core.redis import get_redis_client
from app.core.security import decode_access_token
from app.shared_kernel.enums import RoleEnum

router = APIRouter(prefix="/jobs", tags=["messaging"])
# Own prefix: under /jobs, the jobs router's GET /{job_id} would swallow it.
inbox_router = APIRouter(prefix="/messages", tags=["messaging"])

_WS_UNAUTHORIZED = 4401
_WS_FORBIDDEN = 4403
_WS_NOT_FOUND = 4404
_HEARTBEAT_SECONDS = 25
_HEARTBEAT_FRAME = '{"type":"ping"}'
tracer = trace.get_tracer(__name__)


@router.post("/{job_id}/messages", response_model=MessageOut, status_code=status.HTTP_201_CREATED)
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
        sender_capabilities=current_user.capabilities,
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
        current_user.capabilities,
        limit=pagination.limit,
        offset=pagination.offset,
    )


@inbox_router.get("/unread", response_model=list[ConversationUnreadOut])
async def get_unread_summary(
    current_user: Person = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> list[ConversationUnread]:
    """Every conversation this user is in, newest activity first, with how
    many messages they haven't read. Drives the Messages badge and inbox."""
    with tracer.start_as_current_span("messaging.unread_summary") as span:
        summary = await unread_summary(db, current_user.id)
        span.set_attribute("messaging.conversations", len(summary))
        span.set_attribute("messaging.unread_total", sum(item.unread_count for item in summary))
        return summary


@router.post("/{job_id}/messages/read", status_code=status.HTTP_204_NO_CONTENT)
async def mark_messages_read(
    job_id: uuid.UUID,
    current_user: Person = Depends(get_current_user),
    use_case: MarkMessagesReadUseCase = Depends(get_mark_messages_read_use_case),
) -> None:
    await use_case.execute(job_id, current_user.id, current_user.capabilities)


async def _socket_close_code(job_id: uuid.UUID, token: str) -> int | None:
    """Authenticate the socket and check the caller is a party to the job.

    Runs in its own short-lived session that is closed *before* the socket
    is accepted. Using request-scoped repositories here kept a pooled DB
    connection "idle in transaction" for the socket's whole life; ~15 open
    chats exhausted the pool and every HTTP request (sending, polling,
    marking read) then failed after a 30 s wait. Returns a close code, or
    None when the caller may connect."""
    async with AsyncSessionLocal() as session:
        persons = SqlAlchemyPersonRepository(session)
        jobs = SqlAlchemyJobRepository(session)
        offers = SqlAlchemyJobOfferRepository(session)
        try:
            payload = decode_access_token(token)
            phone = payload.get("sub")
            user = await persons.get_by_phone(phone) if isinstance(phone, str) else None
        except jwt.PyJWTError:
            user = None
        if user is None:
            return _WS_UNAUTHORIZED

        job = await jobs.get(job_id)
        if job is None:
            return _WS_NOT_FOUND

        is_party = user.id in (job.buyer_id, job.worker_id)
        # Same rule as messaging's _require_job_party: an offer only makes a
        # worker a party while the job is still open for offers, so losing
        # bidders can't keep listening once someone else is booked. Checked
        # against capabilities, not active mode, so switching mode never
        # drops access to a conversation the account is still a party to.
        if (
            not is_party
            and user.acts_as(RoleEnum.WORKER)
            and job.status in (JobStatusEnum.REQUESTED, JobStatusEnum.MATCHED)
        ):
            is_party = user.id in await offers.get_for_job(job_id)
        if not is_party and not user.acts_as(RoleEnum.OPS):
            return _WS_FORBIDDEN
    return None


@router.websocket("/{job_id}/ws")
async def chat_socket(
    websocket: WebSocket,
    job_id: uuid.UUID,
    token: str,
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
    close_code = await _socket_close_code(job_id, token)
    if close_code is not None:
        await websocket.close(code=close_code)
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

    async def heartbeat() -> None:
        # Mobile NATs, carriers and proxies silently drop idle sockets; the
        # client treats a missing heartbeat as a dead connection and reconnects.
        while True:
            await asyncio.sleep(_HEARTBEAT_SECONDS)
            await websocket.send_text(_HEARTBEAT_FRAME)

    forward_task = asyncio.create_task(forward_messages())
    disconnect_task = asyncio.create_task(wait_for_disconnect())
    heartbeat_task = asyncio.create_task(heartbeat())

    try:
        await asyncio.wait(
            [forward_task, disconnect_task, heartbeat_task], return_when=asyncio.FIRST_COMPLETED
        )
    finally:
        forward_task.cancel()
        disconnect_task.cancel()
        heartbeat_task.cancel()
        await pubsub.unsubscribe(channel_name(job_id))
        await pubsub.aclose()  # type: ignore[no-untyped-call]
