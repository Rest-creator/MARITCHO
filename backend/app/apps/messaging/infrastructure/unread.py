"""Unread-message summary for one user, across every conversation they're in.

Backs the Messages badge and inbox ordering. Before this there was no way
to learn about a new message unless that chat was open.
"""

import uuid
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import and_, exists, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.apps.jobs.domain.entities import JobStatusEnum
from app.apps.jobs.infrastructure.models import JobModel, JobOfferModel
from app.apps.messaging.infrastructure.models import MessageModel
from app.shared_kernel.clock import as_utc

_PREVIEW_CHARS = 80


@dataclass(frozen=True)
class ConversationUnread:
    job_id: uuid.UUID
    unread_count: int
    last_message_at: datetime | None
    last_message_preview: str | None
    last_sender_id: uuid.UUID | None


def _preview(message_type: str, body: str | None) -> str:
    if body:
        text = " ".join(body.split())
        return text if len(text) <= _PREVIEW_CHARS else f"{text[: _PREVIEW_CHARS - 1]}…"
    return {"VOICE_NOTE": "Voice note", "PHOTO": "Photo", "LOCATION": "Location"}.get(
        message_type, "Message"
    )


async def unread_summary(db: AsyncSession, user_id: uuid.UUID) -> list[ConversationUnread]:
    """Conversations with at least one message, newest activity first.

    A user is in a conversation as the job's buyer, its booked worker, or a
    worker with an offer on it *while the job is still open for offers*
    (same rule as messaging's _require_job_party): once someone else is
    booked, a losing bidder must not see counts or previews."""
    is_party = or_(
        JobModel.buyer_id == user_id,
        JobModel.worker_id == user_id,
        and_(
            JobModel.status.in_([JobStatusEnum.REQUESTED, JobStatusEnum.MATCHED]),
            exists().where(
                and_(JobOfferModel.job_id == JobModel.id, JobOfferModel.worker_id == user_id)
            ),
        ),
    )
    unread_count = func.count(MessageModel.id).filter(
        and_(MessageModel.sender_id != user_id, MessageModel.read_at.is_(None))
    )
    rows = (
        await db.execute(
            select(
                MessageModel.job_id,
                unread_count.label("unread_count"),
                func.max(MessageModel.created_at).label("last_message_at"),
            )
            .join(JobModel, JobModel.id == MessageModel.job_id)
            .where(is_party)
            .group_by(MessageModel.job_id)
            .order_by(func.max(MessageModel.created_at).desc())
            .limit(100)
        )
    ).all()
    if not rows:
        return []

    job_ids = [row.job_id for row in rows]
    latest_rank = (
        func.row_number()
        .over(
            partition_by=MessageModel.job_id,
            order_by=(MessageModel.created_at.desc(), MessageModel.id.desc()),
        )
        .label("rank")
    )
    latest = (
        select(
            MessageModel.job_id,
            MessageModel.message_type,
            MessageModel.body,
            MessageModel.sender_id,
            latest_rank,
        )
        .where(MessageModel.job_id.in_(job_ids))
        .subquery()
    )
    last_by_job = {
        row.job_id: row
        for row in (await db.execute(select(latest).where(latest.c.rank == 1))).all()
    }

    summary: list[ConversationUnread] = []
    for row in rows:
        last = last_by_job.get(row.job_id)
        summary.append(
            ConversationUnread(
                job_id=row.job_id,
                unread_count=int(row.unread_count),
                last_message_at=as_utc(row.last_message_at),
                last_message_preview=(
                    _preview(last.message_type.value, last.body) if last is not None else None
                ),
                last_sender_id=last.sender_id if last is not None else None,
            )
        )
    return summary
