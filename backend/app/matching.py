import uuid
from collections import defaultdict
from collections.abc import Iterable
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.geo import BAND_RANK, classify_distance
from app.models import (
    GradeEnum,
    Job,
    JobStatusEnum,
    Person,
    RoleEnum,
    ServiceArea,
    Skill,
    Standing,
    Suburb,
)
from app.schemas import DistanceBandEnum, MatchCandidateOut

MAX_CANDIDATES = 3

# A worker already tied to one of these job states is not available for a new match.
JOB_BUSY_STATUSES = (
    JobStatusEnum.MATCHED,
    JobStatusEnum.BOOKED,
    JobStatusEnum.IN_PROGRESS,
    JobStatusEnum.DISPUTED,
)

_GRADE_RANK = {
    GradeEnum.REGISTERED: 0,
    GradeEnum.IDENTIFIED: 1,
    GradeEnum.APPRENTICE: 2,
    GradeEnum.JOURNEYMAN: 3,
    GradeEnum.EXPERT: 4,
}

_DEFAULT_GRADE = GradeEnum.REGISTERED
_DEFAULT_ON_TIME_RATE = Decimal("100.00")
_DEFAULT_DISPUTE_RATE = Decimal("0.00")
_DEFAULT_FILL_RATE = Decimal("0.00")


def _standing_score(
    grade: GradeEnum, on_time_rate: Decimal, dispute_rate: Decimal, fill_rate: Decimal
) -> Decimal:
    grade_bonus = Decimal(_GRADE_RANK.get(grade, 0)) * Decimal(10)
    return on_time_rate - dispute_rate + fill_rate + grade_bonus


async def is_worker_busy(db: AsyncSession, worker_id: uuid.UUID) -> bool:
    """True if this worker is already tied to another active (non-terminal) job."""
    result = await db.execute(
        select(Job.id)
        .where(Job.worker_id == worker_id, Job.status.in_(JOB_BUSY_STATUSES))
        .limit(1)
    )
    return result.first() is not None


async def get_busy_worker_ids(
    db: AsyncSession, worker_ids: Iterable[uuid.UUID]
) -> set[uuid.UUID]:
    """Batched form of is_worker_busy: which of these workers are busy, in one query.

    Avoids an N+1 query per candidate when checking a whole pool of workers at
    once (e.g. crew matching), by returning the busy subset up front so
    callers can do an in-memory membership check per candidate instead.
    """
    result = await db.execute(
        select(Job.worker_id.distinct()).where(
            Job.worker_id.in_(worker_ids), Job.status.in_(JOB_BUSY_STATUSES)
        )
    )
    return {worker_id for worker_id in result.scalars().all() if worker_id is not None}


async def is_worker_disputed(db: AsyncSession, worker_id: uuid.UUID) -> bool:
    """True if this worker has any job currently under an open dispute.

    Standing is frozen (not dropped) while this is true, per the "design for
    the worker's worst day" rule.
    """
    result = await db.execute(
        select(Job.id)
        .where(Job.worker_id == worker_id, Job.status == JobStatusEnum.DISPUTED)
        .limit(1)
    )
    return result.first() is not None


async def find_top_candidates(db: AsyncSession, job: Job) -> list[MatchCandidateOut]:
    """Return up to MAX_CANDIDATES workers for a job, ranked by proximity then standing.

    Eligibility: WORKER role, a registered skill in the job's trade, at least
    one declared service area within MODERATE distance of the job's suburb,
    and not currently tied to another job in an active (non-terminal) state.
    Ranking: closer distance band first, standing score as the tiebreaker
    within a band.
    """
    busy_subquery = (
        select(Job.id)
        .where(Job.worker_id == Person.id, Job.status.in_(JOB_BUSY_STATUSES))
        .correlate(Person)
        .exists()
    )

    worker_stmt = select(Person).where(
        Person.role == RoleEnum.WORKER,
        Skill.trade == job.trade,
        Skill.worker_id == Person.id,
        ~busy_subquery,
    )
    workers = (await db.execute(worker_stmt)).scalars().all()
    if not workers:
        return []

    worker_ids = [worker.id for worker in workers]

    areas_result = await db.execute(
        select(ServiceArea).where(ServiceArea.worker_id.in_(worker_ids))
    )
    areas_by_worker: dict[uuid.UUID, list[ServiceArea]] = defaultdict(list)
    for area in areas_result.scalars().all():
        areas_by_worker[area.worker_id].append(area)

    standings_result = await db.execute(
        select(Standing).where(Standing.worker_id.in_(worker_ids))
    )
    standing_by_worker = {s.worker_id: s for s in standings_result.scalars().all()}

    suburb_names = {job.suburb} | {
        area.suburb for areas in areas_by_worker.values() for area in areas
    }
    suburbs_result = await db.execute(select(Suburb).where(Suburb.name.in_(suburb_names)))
    coords = {s.name: (s.latitude, s.longitude) for s in suburbs_result.scalars().all()}

    ranked: list[tuple[tuple[int, Decimal], MatchCandidateOut]] = []
    for person in workers:
        areas = areas_by_worker.get(person.id, [])
        if not areas:
            continue

        best: tuple[int, float, DistanceBandEnum, ServiceArea] | None = None
        for area in areas:
            band, km = classify_distance(job.suburb, area.suburb, coords)
            rank = BAND_RANK[band]
            if best is None or (rank, km) < (best[0], best[1]):
                best = (rank, km, band, area)

        assert best is not None, "areas is non-empty, so best must be set"
        band_rank, km, band, area = best
        if band == DistanceBandEnum.FAR:
            continue

        standing = standing_by_worker.get(person.id)
        grade = standing.grade if standing and standing.grade else _DEFAULT_GRADE
        on_time_rate = (
            standing.on_time_rate
            if standing and standing.on_time_rate is not None
            else _DEFAULT_ON_TIME_RATE
        )
        dispute_rate = (
            standing.dispute_rate
            if standing and standing.dispute_rate is not None
            else _DEFAULT_DISPUTE_RATE
        )
        fill_rate = (
            standing.fill_rate
            if standing and standing.fill_rate is not None
            else _DEFAULT_FILL_RATE
        )
        jobs_completed = (
            standing.jobs_completed if standing and standing.jobs_completed is not None else 0
        )

        score = _standing_score(grade, on_time_rate, dispute_rate, fill_rate)
        reason = (
            f"{job.trade.value} skill; {area.suburb} is {band.value} ({km:.1f}km) "
            f"to {job.suburb}; grade {grade}, {on_time_rate}% on-time, "
            f"{dispute_rate}% disputed, {fill_rate}% fill rate"
        )

        candidate = MatchCandidateOut(
            worker_id=person.id,
            suburb=area.suburb,
            travel_means=area.travel_means,
            distance_band=band,
            distance_km=round(km, 1),
            grade=grade,
            on_time_rate=on_time_rate,
            dispute_rate=dispute_rate,
            fill_rate=fill_rate,
            jobs_completed=jobs_completed,
            reason=reason,
        )
        ranked.append(((band_rank, -score), candidate))

    ranked.sort(key=lambda pair: pair[0])
    return [candidate for _, candidate in ranked[:MAX_CANDIDATES]]
