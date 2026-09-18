import uuid
from collections.abc import Sequence
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal

from app.apps.accounts.domain.repositories import PersonRepository
from app.apps.workers.domain.entities import (
    ServiceArea,
    Skill,
    StandingView,
    WorkerReference,
    WorkerVettingView,
    WorkerVouch,
)
from app.apps.workers.domain.repositories import (
    ServiceAreaRepository,
    SkillRepository,
    StandingRepository,
    WorkerReferenceRepository,
    WorkerVettingRepository,
    WorkerVouchRepository,
)
from app.core.exceptions import (
    ConflictError,
    ForbiddenError,
    IntegrityConflictError,
    ValidationConflictError,
)
from app.shared_kernel.enums import GradeEnum, RoleEnum, TradeEnum
from app.shared_kernel.grading import GRADE_RANK, meets_minimum_grade
from app.shared_kernel.ports import SuburbLookupPort, WorkerAvailabilityPort, WorkerJobStatsPort
from app.shared_kernel.unit_of_work import UnitOfWork

_DEFAULT_ON_TIME_RATE = Decimal("100.00")
_DEFAULT_DISPUTE_RATE = Decimal("0.00")
_DEFAULT_FILL_RATE = Decimal("0.00")

# Progressive vetting tiers (ADR-005) — evidence-based thresholds that
# replace institution-dependent checks (credit bureaus, court records) that
# don't exist or aren't queryable in this market.
MIN_REFERENCES_FOR_APPRENTICE = 1
MIN_VOUCHES_FOR_JOURNEYMAN = 1
MIN_VOUCHES_FOR_EXPERT = 3
# A vouch only counts from a worker whose current grade is at least this.
# ADR-005 also calls for excluding vouchers with "prior flagged fraudulent-
# vouch strikes" — no such strike/flagging mechanism exists yet (no
# observed abuse pattern to design against yet); only the grade-floor
# check below is enforced today. Revisit once real vouch-fraud patterns
# emerge.
VOUCHER_MINIMUM_GRADE = GradeEnum.JOURNEYMAN
_QUALIFYING_VOUCHER_GRADES = {
    grade for grade in GradeEnum if GRADE_RANK[grade] >= GRADE_RANK[VOUCHER_MINIMUM_GRADE]
}


def _pct(numerator: int, denominator: int, default: Decimal) -> Decimal:
    if denominator <= 0:
        return default
    return (Decimal(numerator) / Decimal(denominator) * 100).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )


class RegisterSkillUseCase:
    def __init__(
        self, skills: SkillRepository, standings: StandingRepository, uow: UnitOfWork
    ) -> None:
        self._skills = skills
        self._standings = standings
        self._uow = uow

    async def execute(
        self, worker_id: uuid.UUID, trade: TradeEnum, proof_url: str | None
    ) -> Skill:
        try:
            skill = await self._skills.add(worker_id=worker_id, trade=trade, proof_url=proof_url)
        except IntegrityConflictError as exc:
            raise ConflictError("Skill already registered for this trade") from exc
        await self._standings.ensure(worker_id)
        await self._uow.commit()
        return skill


class ListMySkillsUseCase:
    def __init__(self, skills: SkillRepository) -> None:
        self._skills = skills

    async def execute(self, worker_id: uuid.UUID, *, limit: int, offset: int) -> Sequence[Skill]:
        return await self._skills.list_by_worker(worker_id, limit=limit, offset=offset)


class RegisterServiceAreaUseCase:
    def __init__(
        self,
        service_areas: ServiceAreaRepository,
        standings: StandingRepository,
        suburbs: SuburbLookupPort,
        uow: UnitOfWork,
    ) -> None:
        self._service_areas = service_areas
        self._standings = standings
        self._suburbs = suburbs
        self._uow = uow

    async def execute(
        self, worker_id: uuid.UUID, suburb: str, travel_means: str | None
    ) -> ServiceArea:
        if not await self._suburbs.exists(suburb):
            raise ValidationConflictError("Unknown suburb")

        try:
            area = await self._service_areas.add(
                worker_id=worker_id, suburb=suburb, travel_means=travel_means
            )
        except IntegrityConflictError as exc:
            raise ConflictError("Service area already registered for this suburb") from exc
        await self._standings.ensure(worker_id)
        await self._uow.commit()
        return area


class ListMyServiceAreasUseCase:
    def __init__(self, service_areas: ServiceAreaRepository) -> None:
        self._service_areas = service_areas

    async def execute(
        self, worker_id: uuid.UUID, *, limit: int, offset: int
    ) -> Sequence[ServiceArea]:
        return await self._service_areas.list_by_worker(worker_id, limit=limit, offset=offset)


class GetStandingUseCase:
    def __init__(self, standings: StandingRepository, availability: WorkerAvailabilityPort) -> None:
        self._standings = standings
        self._availability = availability

    async def execute(self, worker_id: uuid.UUID) -> StandingView:
        standing = await self._standings.get(worker_id)
        frozen = await self._availability.is_worker_disputed(worker_id)

        if standing is not None:
            return StandingView(
                worker_id=standing.worker_id,
                grade=standing.grade or GradeEnum.REGISTERED,
                on_time_rate=(
                    standing.on_time_rate
                    if standing.on_time_rate is not None
                    else _DEFAULT_ON_TIME_RATE
                ),
                dispute_rate=(
                    standing.dispute_rate
                    if standing.dispute_rate is not None
                    else _DEFAULT_DISPUTE_RATE
                ),
                fill_rate=(
                    standing.fill_rate if standing.fill_rate is not None else _DEFAULT_FILL_RATE
                ),
                jobs_completed=(
                    standing.jobs_completed if standing.jobs_completed is not None else 0
                ),
                is_frozen=frozen,
            )

        # A worker with nothing registered yet still has a "computed"
        # standing: the same defaults the standings table would give them
        # on first insert.
        return StandingView(
            worker_id=worker_id,
            grade=GradeEnum.REGISTERED,
            on_time_rate=_DEFAULT_ON_TIME_RATE,
            dispute_rate=_DEFAULT_DISPUTE_RATE,
            fill_rate=_DEFAULT_FILL_RATE,
            jobs_completed=0,
            is_frozen=frozen,
        )


class RecomputeStandingUseCase:
    """Recompute a worker's Standing from their actual Job/Dispute history
    (via WorkerJobStatsPort, owned by the jobs app).

    Standing is computed, never assigned (per the PRD): this always
    derives the full current truth rather than incrementing counters, so
    it can never drift out of sync with reality.

    Only covers individual (Quick Hire) jobs. Crew order completions are
    not attributed to a specific member's standing — crew booking commits
    the whole crew as one unit and doesn't track which members actually
    worked.

    Does not commit — called from within the jobs app's CompleteJobUseCase/
    RaiseDisputeUseCase, which commit once at the end of their own
    transaction. Does not touch `grade`: no documented rule specifies
    grade-progression thresholds from job history: see RecomputeGradeUseCase
    for the vetting-evidence-based grade progression that does exist.
    """

    def __init__(self, standings: StandingRepository, job_stats: WorkerJobStatsPort) -> None:
        self._standings = standings
        self._job_stats = job_stats

    async def execute(self, worker_id: uuid.UUID) -> None:
        standing = await self._standings.get(worker_id)
        if standing is None:
            # A worker can't be booked without first registering a skill,
            # which always creates a Standing row — so this shouldn't
            # happen, but there's nothing to recompute onto if it does.
            return

        stats = await self._job_stats.get_stats(worker_id)

        standing.jobs_completed = stats.total_completed
        standing.fill_rate = _pct(stats.total_completed, stats.total_booked, _DEFAULT_FILL_RATE)
        standing.dispute_rate = _pct(
            stats.total_disputed, stats.total_booked, _DEFAULT_DISPUTE_RATE
        )
        standing.on_time_rate = _pct(
            stats.total_completed - stats.total_completed_and_disputed,
            stats.total_completed,
            _DEFAULT_ON_TIME_RATE,
        )
        await self._standings.save(standing)


class RecomputeGradeUseCase:
    """Recompute a worker's Standing.grade from accumulated vetting evidence.

    Like RecomputeStandingUseCase, this fully re-derives the value from
    source evidence every time, never incrementing — it can't drift.
    Thresholds:
    - IDENTIFIED: a photographed national ID has been submitted.
    - APPRENTICE: IDENTIFIED, plus at least one contactable reference.
    - JOURNEYMAN: at least one vouch from a worker whose *current* grade
      is JOURNEYMAN or EXPERT.
    - EXPERT: at least three such vouches.

    A vouch's validity is re-checked against the voucher's current grade
    every time (not a snapshot taken at vouch time). Does not commit — the
    calling use case commits once at the end of its own transaction.
    """

    def __init__(
        self,
        standings: StandingRepository,
        vetting: WorkerVettingRepository,
        references: WorkerReferenceRepository,
        vouches: WorkerVouchRepository,
    ) -> None:
        self._standings = standings
        self._vetting = vetting
        self._references = references
        self._vouches = vouches

    async def execute(self, worker_id: uuid.UUID) -> None:
        standing = await self._standings.get(worker_id)
        if standing is None:
            return

        vetting = await self._vetting.get(worker_id)
        has_id_photo = vetting is not None and vetting.id_photo_url is not None

        reference_count = await self._references.count_by_worker(worker_id)
        valid_vouch_count = await self._vouches.count_valid_vouches(
            worker_id, _QUALIFYING_VOUCHER_GRADES
        )

        if valid_vouch_count >= MIN_VOUCHES_FOR_EXPERT:
            grade = GradeEnum.EXPERT
        elif valid_vouch_count >= MIN_VOUCHES_FOR_JOURNEYMAN:
            grade = GradeEnum.JOURNEYMAN
        elif has_id_photo and reference_count >= MIN_REFERENCES_FOR_APPRENTICE:
            grade = GradeEnum.APPRENTICE
        elif has_id_photo:
            grade = GradeEnum.IDENTIFIED
        else:
            grade = GradeEnum.REGISTERED

        standing.grade = grade
        await self._standings.save(standing)


class GetVettingViewUseCase:
    def __init__(
        self,
        vetting: WorkerVettingRepository,
        references: WorkerReferenceRepository,
        vouches: WorkerVouchRepository,
        standings: StandingRepository,
    ) -> None:
        self._vetting = vetting
        self._references = references
        self._vouches = vouches
        self._standings = standings

    async def execute(self, worker_id: uuid.UUID) -> WorkerVettingView:
        vetting = await self._vetting.get(worker_id)
        standing = await self._standings.get(worker_id)
        reference_count = await self._references.count_by_worker(worker_id)
        vouch_count = await self._vouches.count_by_worker(worker_id)
        return WorkerVettingView(
            worker_id=worker_id,
            id_photo_url=vetting.id_photo_url if vetting else None,
            id_submitted_at=vetting.id_submitted_at if vetting else None,
            reference_count=reference_count,
            vouch_count=vouch_count,
            grade=(standing.grade if standing and standing.grade else GradeEnum.REGISTERED),
        )


class SubmitIdPhotoUseCase:
    """Gates REGISTERED -> IDENTIFIED (ADR-005). Grade is recomputed
    immediately, same transaction, from all accumulated evidence."""

    def __init__(
        self,
        vetting: WorkerVettingRepository,
        standings: StandingRepository,
        uow: UnitOfWork,
        recompute_grade: RecomputeGradeUseCase,
        view: GetVettingViewUseCase,
    ) -> None:
        self._vetting = vetting
        self._standings = standings
        self._uow = uow
        self._recompute_grade = recompute_grade
        self._view = view

    async def execute(self, worker_id: uuid.UUID, id_photo_url: str) -> WorkerVettingView:
        await self._vetting.upsert_id_photo(worker_id, id_photo_url, datetime.utcnow())
        await self._standings.ensure(worker_id)
        await self._recompute_grade.execute(worker_id)
        await self._uow.commit()
        return await self._view.execute(worker_id)


class AddReferenceUseCase:
    """Gates IDENTIFIED -> APPRENTICE (ADR-005)."""

    def __init__(
        self,
        references: WorkerReferenceRepository,
        standings: StandingRepository,
        uow: UnitOfWork,
        recompute_grade: RecomputeGradeUseCase,
    ) -> None:
        self._references = references
        self._standings = standings
        self._uow = uow
        self._recompute_grade = recompute_grade

    async def execute(self, worker_id: uuid.UUID, name: str, phone: str) -> WorkerReference:
        reference = await self._references.add(worker_id=worker_id, name=name, phone=phone)
        await self._standings.ensure(worker_id)
        await self._recompute_grade.execute(worker_id)
        await self._uow.commit()
        return reference


class ListMyReferencesUseCase:
    def __init__(self, references: WorkerReferenceRepository) -> None:
        self._references = references

    async def execute(
        self, worker_id: uuid.UUID, *, limit: int, offset: int
    ) -> Sequence[WorkerReference]:
        return await self._references.list_by_worker(worker_id, limit=limit, offset=offset)


class VouchForWorkerUseCase:
    """A JOURNEYMAN+ worker vouches for another. Gates APPRENTICE ->
    JOURNEYMAN/EXPERT (ADR-005). Recomputes the *vouched-for* worker's
    grade, not the voucher's."""

    def __init__(
        self,
        persons: PersonRepository,
        standings: StandingRepository,
        vouches: WorkerVouchRepository,
        uow: UnitOfWork,
        recompute_grade: RecomputeGradeUseCase,
    ) -> None:
        self._persons = persons
        self._standings = standings
        self._vouches = vouches
        self._uow = uow
        self._recompute_grade = recompute_grade

    async def execute(self, *, voucher_id: uuid.UUID, target_worker_id: uuid.UUID) -> WorkerVouch:
        if target_worker_id == voucher_id:
            raise ValidationConflictError("Cannot vouch for yourself")

        target = await self._persons.get_by_id(target_worker_id)
        if target is None or target.role != RoleEnum.WORKER:
            raise ValidationConflictError("worker_id does not refer to a registered worker")

        voucher_standing = await self._standings.get(voucher_id)
        voucher_grade = (
            voucher_standing.grade
            if voucher_standing and voucher_standing.grade
            else GradeEnum.REGISTERED
        )
        if not meets_minimum_grade(voucher_grade, VOUCHER_MINIMUM_GRADE):
            raise ForbiddenError(
                f"Only {VOUCHER_MINIMUM_GRADE.value}+ workers may vouch for others"
            )

        try:
            vouch = await self._vouches.add(worker_id=target_worker_id, voucher_id=voucher_id)
        except IntegrityConflictError as exc:
            raise ConflictError("You have already vouched for this worker") from exc

        await self._recompute_grade.execute(target_worker_id)
        await self._uow.commit()
        return vouch
