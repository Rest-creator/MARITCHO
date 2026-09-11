import uuid
from collections import defaultdict
from collections.abc import Iterable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.geo import BAND_RANK, classify_distance
from app.matching import get_busy_worker_ids
from app.models import Crew, CrewMember, CrewOrder, CrewOrderStatusEnum, ServiceArea, Skill, Suburb
from app.schemas import CrewMatchCandidateOut, DistanceBandEnum

MAX_CREW_CANDIDATES = 3

# A crew already tied to one of these order states can't take on a new one.
_CREW_BUSY_STATUSES = (CrewOrderStatusEnum.BOOKED, CrewOrderStatusEnum.IN_PROGRESS)


async def is_crew_busy(db: AsyncSession, crew_id: uuid.UUID) -> bool:
    """True if this crew is already committed to another active crew order.

    A crew is booked as a whole: there's no sub-crew assignment model, so a
    crew can only serve one active order at a time.
    """
    result = await db.execute(
        select(CrewOrder.id)
        .where(CrewOrder.crew_id == crew_id, CrewOrder.status.in_(_CREW_BUSY_STATUSES))
        .limit(1)
    )
    return result.first() is not None


async def get_busy_crew_ids(db: AsyncSession, crew_ids: Iterable[uuid.UUID]) -> set[uuid.UUID]:
    """Batched form of is_crew_busy: which of these crews are busy, in one query.

    Avoids an N+1 query per crew when checking a whole pool at once.
    """
    result = await db.execute(
        select(CrewOrder.crew_id.distinct()).where(
            CrewOrder.crew_id.in_(crew_ids), CrewOrder.status.in_(_CREW_BUSY_STATUSES)
        )
    )
    return {crew_id for crew_id in result.scalars().all() if crew_id is not None}


async def find_top_crew_candidates(
    db: AsyncSession, order: CrewOrder
) -> list[CrewMatchCandidateOut]:
    """Return up to MAX_CREW_CANDIDATES crews able to fill a crew order.

    A crew qualifies if it has at least `workers_needed` members with a
    skill in the order's trade, a service area within MODERATE distance of
    the order's suburb, and who aren't individually busy on another job —
    and the crew itself isn't already committed to another active order.
    Ranking: closer distance band first, more qualifying members as the
    tiebreaker within a band.
    """
    crews = (await db.execute(select(Crew))).scalars().all()
    if not crews:
        return []

    crew_ids = [crew.id for crew in crews]

    members_result = await db.execute(select(CrewMember).where(CrewMember.crew_id.in_(crew_ids)))
    member_ids_by_crew: dict[uuid.UUID, list[uuid.UUID]] = defaultdict(list)
    all_worker_ids: set[uuid.UUID] = set()
    for member in members_result.scalars().all():
        member_ids_by_crew[member.crew_id].append(member.worker_id)
        all_worker_ids.add(member.worker_id)

    if not all_worker_ids:
        return []

    skills_result = await db.execute(
        select(Skill).where(Skill.worker_id.in_(all_worker_ids), Skill.trade == order.trade)
    )
    skilled_worker_ids = {skill.worker_id for skill in skills_result.scalars().all()}
    if not skilled_worker_ids:
        return []

    areas_result = await db.execute(
        select(ServiceArea).where(ServiceArea.worker_id.in_(skilled_worker_ids))
    )
    areas_by_worker: dict[uuid.UUID, list[ServiceArea]] = defaultdict(list)
    for area in areas_result.scalars().all():
        areas_by_worker[area.worker_id].append(area)

    suburb_names = {order.suburb} | {
        area.suburb for areas in areas_by_worker.values() for area in areas
    }
    suburbs_result = await db.execute(select(Suburb).where(Suburb.name.in_(suburb_names)))
    coords = {s.name: (s.latitude, s.longitude) for s in suburbs_result.scalars().all()}

    busy_worker_ids = await get_busy_worker_ids(db, skilled_worker_ids)

    far_rank = BAND_RANK[DistanceBandEnum.FAR]
    worker_band: dict[uuid.UUID, tuple[int, float]] = {}
    for worker_id in skilled_worker_ids:
        areas = areas_by_worker.get(worker_id, [])
        if not areas or worker_id in busy_worker_ids:
            continue

        best = None
        for area in areas:
            band, km = classify_distance(order.suburb, area.suburb, coords)
            rank = BAND_RANK[band]
            if best is None or (rank, km) < best:
                best = (rank, km)

        if best is not None and best[0] < far_rank:
            worker_band[worker_id] = best

    busy_crew_ids = await get_busy_crew_ids(db, crew_ids)

    ranked: list[tuple[tuple[int, int], CrewMatchCandidateOut]] = []
    for crew in crews:
        if crew.id in busy_crew_ids:
            continue

        member_ids = member_ids_by_crew.get(crew.id, [])
        qualifying = [worker_id for worker_id in member_ids if worker_id in worker_band]
        if len(qualifying) < order.workers_needed:
            continue

        best_band_rank, best_km = min(worker_band[worker_id] for worker_id in qualifying)
        band = next(b for b, rank in BAND_RANK.items() if rank == best_band_rank)

        reason = (
            f"{len(qualifying)} of {len(member_ids)} members have {order.trade.value} "
            f"skill within {band.value} ({best_km:.1f}km) of {order.suburb}"
        )

        candidate = CrewMatchCandidateOut(
            crew_id=crew.id,
            crew_name=crew.name,
            lead_id=crew.lead_id,
            qualifying_members=len(qualifying),
            total_members=len(member_ids),
            distance_band=band,
            distance_km=round(best_km, 1),
            reason=reason,
        )
        ranked.append(((best_band_rank, -len(qualifying)), candidate))

    ranked.sort(key=lambda pair: pair[0])
    return [candidate for _, candidate in ranked[:MAX_CREW_CANDIDATES]]
