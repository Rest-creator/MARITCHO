import uuid

from app.apps.crews.domain.entities import CrewMatchCandidate, CrewOrder
from app.apps.crews.domain.repositories import (
    CrewMemberRepository,
    CrewOrderRepository,
    CrewRepository,
)
from app.shared_kernel.enums import DistanceBandEnum
from app.shared_kernel.geo import BAND_RANK, classify_distance
from app.shared_kernel.ports import (
    SuburbLookupPort,
    WorkerAvailabilityPort,
    WorkerMatchingProfilePort,
)

MAX_CREW_CANDIDATES = 3


class CrewMatchingService:
    """Ranks up to MAX_CREW_CANDIDATES crews able to fill a crew order.

    A crew qualifies if it has at least `workers_needed` members with a
    skill in the order's trade, a service area within MODERATE distance of
    the order's suburb, and who aren't individually busy on another job —
    and the crew itself isn't already committed to another active order.
    Ranking: closer distance band first, more qualifying members as the
    tiebreaker within a band.

    Cross-app data (skills/service-areas) comes through
    WorkerMatchingProfilePort (owned by the workers app); individual
    worker-busy filtering comes through WorkerAvailabilityPort (owned by
    the jobs app, since Quick Hire jobs are what make a worker busy);
    suburb coordinates come through SuburbLookupPort (owned by the suburbs
    app). Crew-busy filtering stays in-app via CrewOrderRepository, since
    crews owns that state.
    """

    def __init__(
        self,
        crews: CrewRepository,
        crew_members: CrewMemberRepository,
        crew_orders: CrewOrderRepository,
        worker_profiles: WorkerMatchingProfilePort,
        worker_availability: WorkerAvailabilityPort,
        suburbs: SuburbLookupPort,
    ) -> None:
        self._crews = crews
        self._crew_members = crew_members
        self._crew_orders = crew_orders
        self._worker_profiles = worker_profiles
        self._worker_availability = worker_availability
        self._suburbs = suburbs

    async def find_top_candidates(self, order: CrewOrder) -> list[CrewMatchCandidate]:
        crews = await self._crews.list_all()
        if not crews:
            return []

        crew_ids = [crew.id for crew in crews]
        member_ids_by_crew = await self._crew_members.list_worker_ids_by_crews(crew_ids)
        all_worker_ids: set[uuid.UUID] = {
            worker_id for worker_ids in member_ids_by_crew.values() for worker_id in worker_ids
        }
        if not all_worker_ids:
            return []

        skilled_ids_with_trade = await self._worker_profiles.get_worker_ids_with_skill(order.trade)
        skilled_worker_ids = all_worker_ids & skilled_ids_with_trade
        if not skilled_worker_ids:
            return []

        areas_by_worker = await self._worker_profiles.get_service_areas(skilled_worker_ids)

        suburb_names = {order.suburb} | {
            area.suburb for areas in areas_by_worker.values() for area in areas
        }
        coords = await self._suburbs.get_coords(suburb_names)

        busy_worker_ids = await self._worker_availability.get_busy_worker_ids(skilled_worker_ids)

        far_rank = BAND_RANK[DistanceBandEnum.FAR]

        worker_band: dict[uuid.UUID, tuple[int, float]] = {}
        for worker_id in skilled_worker_ids:
            areas = areas_by_worker.get(worker_id, [])
            if not areas or worker_id in busy_worker_ids:
                continue

            best: tuple[int, float] | None = None
            for area in areas:
                band, km = classify_distance(order.suburb, area.suburb, coords)
                rank = BAND_RANK[band]
                if best is None or (rank, km) < best:
                    best = (rank, km)

            if best is not None and best[0] < far_rank:
                worker_band[worker_id] = best

        busy_crew_ids = await self._crew_orders.get_busy_crew_ids(crew_ids)

        ranked: list[tuple[tuple[int, int], CrewMatchCandidate]] = []
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

            candidate = CrewMatchCandidate(
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
