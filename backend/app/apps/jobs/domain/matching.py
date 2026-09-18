from decimal import Decimal

from app.apps.jobs.domain.entities import Job, MatchCandidate
from app.apps.jobs.domain.repositories import JobRepository
from app.shared_kernel.enums import DistanceBandEnum, GradeEnum
from app.shared_kernel.geo import BAND_RANK, classify_distance
from app.shared_kernel.grading import GRADE_RANK
from app.shared_kernel.ports import SuburbLookupPort, WorkerMatchingProfilePort
from app.shared_kernel.value_objects import WorkerServiceAreaSnapshot

MAX_CANDIDATES = 3

_DEFAULT_GRADE = GradeEnum.REGISTERED
_DEFAULT_ON_TIME_RATE = Decimal("100.00")
_DEFAULT_DISPUTE_RATE = Decimal("0.00")
_DEFAULT_FILL_RATE = Decimal("0.00")


def _standing_score(
    grade: GradeEnum, on_time_rate: Decimal, dispute_rate: Decimal, fill_rate: Decimal
) -> Decimal:
    grade_bonus = Decimal(GRADE_RANK.get(grade, 0)) * Decimal(10)
    return on_time_rate - dispute_rate + fill_rate + grade_bonus


class JobMatchingService:
    """Ranks up to MAX_CANDIDATES workers for a Quick Hire job.

    Eligibility: a registered skill in the job's trade (workers app), at
    least one declared service area within MODERATE distance of the job's
    suburb, and not currently tied to another job in an active
    (non-terminal) state (this app's own busy check). Ranking: closer
    distance band first, standing score as the tiebreaker within a band.

    Cross-app data (skills/service-areas/standings) comes through
    WorkerMatchingProfilePort (owned by the workers app) and
    SuburbLookupPort (owned by the suburbs app); busy-worker filtering
    stays in-app via JobRepository, since jobs owns WorkerAvailabilityPort.
    """

    def __init__(
        self,
        jobs: JobRepository,
        worker_profiles: WorkerMatchingProfilePort,
        suburbs: SuburbLookupPort,
    ) -> None:
        self._jobs = jobs
        self._worker_profiles = worker_profiles
        self._suburbs = suburbs

    async def find_top_candidates(self, job: Job) -> list[MatchCandidate]:
        worker_ids = await self._worker_profiles.get_worker_ids_with_skill(job.trade)
        if not worker_ids:
            return []

        busy_ids = await self._jobs.get_busy_worker_ids(worker_ids)
        available_ids = worker_ids - busy_ids
        if not available_ids:
            return []

        areas_by_worker = await self._worker_profiles.get_service_areas(available_ids)
        standings_by_worker = await self._worker_profiles.get_standings(available_ids)

        suburb_names = {job.suburb} | {
            area.suburb for areas in areas_by_worker.values() for area in areas
        }
        coords = await self._suburbs.get_coords(suburb_names)

        ranked: list[tuple[tuple[int, Decimal], MatchCandidate]] = []
        for worker_id in available_ids:
            areas = areas_by_worker.get(worker_id, [])
            if not areas:
                continue

            best: tuple[int, float, DistanceBandEnum, WorkerServiceAreaSnapshot] | None = None
            for area in areas:
                band, km = classify_distance(job.suburb, area.suburb, coords)
                rank = BAND_RANK[band]
                if best is None or (rank, km) < (best[0], best[1]):
                    best = (rank, km, band, area)

            assert best is not None, "areas is non-empty, so best must be set"
            band_rank, km, band, area = best
            if band == DistanceBandEnum.FAR:
                continue

            standing = standings_by_worker.get(worker_id)
            grade = standing.grade if standing else _DEFAULT_GRADE
            on_time_rate = standing.on_time_rate if standing else _DEFAULT_ON_TIME_RATE
            dispute_rate = standing.dispute_rate if standing else _DEFAULT_DISPUTE_RATE
            fill_rate = standing.fill_rate if standing else _DEFAULT_FILL_RATE
            jobs_completed = standing.jobs_completed if standing else 0

            score = _standing_score(grade, on_time_rate, dispute_rate, fill_rate)
            reason = (
                f"{job.trade.value} skill; {area.suburb} is {band.value} ({km:.1f}km) "
                f"to {job.suburb}; grade {grade}, {on_time_rate}% on-time, "
                f"{dispute_rate}% disputed, {fill_rate}% fill rate"
            )

            candidate = MatchCandidate(
                worker_id=worker_id,
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
