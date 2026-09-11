import uuid
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Dispute, Job, JobStatusEnum, Standing

_DEFAULT_FILL_RATE = Decimal("0.00")
_DEFAULT_DISPUTE_RATE = Decimal("0.00")
_DEFAULT_ON_TIME_RATE = Decimal("100.00")


def _pct(numerator: int, denominator: int, default: Decimal) -> Decimal:
    if denominator <= 0:
        return default
    return (Decimal(numerator) / Decimal(denominator) * 100).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )


async def recompute_standing(db: AsyncSession, worker_id: uuid.UUID) -> None:
    """Recompute a worker's Standing from their actual Job/Dispute history.

    Standing is computed, never assigned (per the PRD): this always derives
    the full current truth from Job/Dispute rows rather than incrementing
    counters, so it can never drift out of sync with reality.

    Only covers individual (Quick Hire) jobs. Crew order completions are
    not attributed to a specific member's standing, since crew booking
    commits the whole crew as one unit and doesn't track which members
    actually worked (see app/crew_matching.py) — there's no data to
    attribute a crew completion to one worker's individual record yet.

    Does not touch `grade`: no documented rule specifies grade-progression
    thresholds, so grade remains a separate, currently-manual concern.
    """
    standing = await db.get(Standing, worker_id)
    if standing is None:
        # A worker can't be booked without first registering a skill, which
        # always creates a Standing row — so this shouldn't happen, but
        # there's nothing to recompute onto if it somehow does.
        return

    total_booked = await db.scalar(
        select(func.count()).select_from(Job).where(Job.worker_id == worker_id)
    )
    total_completed = await db.scalar(
        select(func.count())
        .select_from(Job)
        .where(Job.worker_id == worker_id, Job.status == JobStatusEnum.COMPLETED)
    )
    total_disputed = await db.scalar(
        select(func.count(func.distinct(Job.id)))
        .select_from(Job)
        .join(Dispute, Dispute.job_id == Job.id)
        .where(Job.worker_id == worker_id)
    )
    total_completed_and_disputed = await db.scalar(
        select(func.count(func.distinct(Job.id)))
        .select_from(Job)
        .join(Dispute, Dispute.job_id == Job.id)
        .where(Job.worker_id == worker_id, Job.status == JobStatusEnum.COMPLETED)
    )

    total_booked = total_booked or 0
    total_completed = total_completed or 0
    total_disputed = total_disputed or 0
    total_completed_and_disputed = total_completed_and_disputed or 0

    standing.jobs_completed = total_completed
    standing.fill_rate = _pct(total_completed, total_booked, _DEFAULT_FILL_RATE)
    standing.dispute_rate = _pct(total_disputed, total_booked, _DEFAULT_DISPUTE_RATE)
    standing.on_time_rate = _pct(
        total_completed - total_completed_and_disputed, total_completed, _DEFAULT_ON_TIME_RATE
    )
