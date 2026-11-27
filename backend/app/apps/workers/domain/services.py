import uuid
from collections.abc import Sequence
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from app.apps.accounts.domain.repositories import PersonRepository
from app.apps.workers.domain.entities import (
    PendingVettingDocument,
    ServiceArea,
    Skill,
    StandingView,
    WorkerDirectoryItem,
    WorkerPublicProfile,
    WorkerReference,
    WorkerVettingView,
    WorkerVouch,
)
from app.apps.workers.domain.identity import (
    hash_id_number,
    media_id_from_url,
    normalize_zim_id_number,
    police_clearance_expiry,
)
from app.apps.workers.domain.repositories import (
    MediaOwnershipRepository,
    ServiceAreaRepository,
    SkillRepository,
    StandingRepository,
    WorkerDirectoryRepository,
    WorkerReferenceRepository,
    WorkerVettingRepository,
    WorkerVouchRepository,
)
from app.core.exceptions import (
    ConflictError,
    ForbiddenError,
    IntegrityConflictError,
    NotFoundError,
    ValidationConflictError,
)
from app.shared_kernel.clock import utcnow
from app.shared_kernel.embeddings import (
    RELEVANCE_THRESHOLD,
    cosine_similarity,
    embed_text,
    infer_best_trade,
    rank_skills_by_query,
    relevance_score,
)
from app.shared_kernel.enums import (
    DistanceBandEnum,
    GradeEnum,
    RoleEnum,
    TradeEnum,
    VerificationStatusEnum,
)
from app.shared_kernel.geo import BAND_RANK, classify_distance
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
        # ADR-010: identity is earned by an OPS-approved ID, not by a photo.
        has_id_photo = vetting is not None and vetting.is_id_verified

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
            police_clearance_url=vetting.police_clearance_url if vetting else None,
            police_clearance_submitted_at=(
                vetting.police_clearance_submitted_at if vetting else None
            ),
            id_status=vetting.id_status if vetting else None,
            id_rejection_reason=vetting.id_rejection_reason if vetting else None,
            id_verified_name=vetting.id_verified_name if vetting else None,
            police_clearance_status=vetting.police_clearance_status if vetting else None,
            police_clearance_rejection_reason=(
                vetting.police_clearance_rejection_reason if vetting else None
            ),
            police_clearance_issued_on=vetting.police_clearance_issued_on if vetting else None,
            police_clearance_expires_on=vetting.police_clearance_expires_on if vetting else None,
            has_police_clearance=vetting.is_police_cleared(utcnow().date()) if vetting else False,
        )


async def _require_owned_photo(
    media: MediaOwnershipRepository, worker_id: uuid.UUID, url: str
) -> str:
    """ADR-010: an identity document must be the worker's own upload, served
    privately from /media/{id}, never an arbitrary link."""
    media_id = media_id_from_url(url)
    if media_id is None or not await media.is_owned_image(media_id, worker_id):
        raise ValidationConflictError(
            "Upload the photo in the app first; only your own uploaded photo can be used."
        )
    return f"/media/{media_id}"


class SubmitIdPhotoUseCase:
    """Submits (or replaces) the ID photo for review (ADR-005, ADR-010). The
    photo goes to PENDING; IDENTIFIED waits for an OPS approval. Grade is
    recomputed in the same transaction (a replaced photo loses the grade
    until it is approved again)."""

    def __init__(
        self,
        vetting: WorkerVettingRepository,
        standings: StandingRepository,
        uow: UnitOfWork,
        recompute_grade: RecomputeGradeUseCase,
        view: GetVettingViewUseCase,
        media: MediaOwnershipRepository,
    ) -> None:
        self._media = media
        self._vetting = vetting
        self._standings = standings
        self._uow = uow
        self._recompute_grade = recompute_grade
        self._view = view

    async def execute(self, worker_id: uuid.UUID, id_photo_url: str) -> WorkerVettingView:
        url = await _require_owned_photo(self._media, worker_id, id_photo_url)
        await self._vetting.upsert_id_photo(worker_id, url, utcnow())
        await self._standings.ensure(worker_id)
        await self._recompute_grade.execute(worker_id)
        await self._uow.commit()
        return await self._view.execute(worker_id)


class SubmitPoliceClearanceUseCase:
    """Submit (or replace) the worker's Police Clearance certificate photo.

    Optional when joining Maritcho. The Police Cleared badge appears only
    once OPS approves it (ADR-010); it no longer counts as identity.
    """

    def __init__(
        self,
        vetting: WorkerVettingRepository,
        standings: StandingRepository,
        uow: UnitOfWork,
        recompute_grade: RecomputeGradeUseCase,
        view: GetVettingViewUseCase,
        media: MediaOwnershipRepository,
    ) -> None:
        self._media = media
        self._vetting = vetting
        self._standings = standings
        self._uow = uow
        self._recompute_grade = recompute_grade
        self._view = view

    async def execute(self, worker_id: uuid.UUID, police_clearance_url: str) -> WorkerVettingView:
        url = await _require_owned_photo(self._media, worker_id, police_clearance_url)
        await self._vetting.upsert_police_clearance(worker_id, url, utcnow())
        await self._standings.ensure(worker_id)
        await self._recompute_grade.execute(worker_id)
        await self._uow.commit()
        return await self._view.execute(worker_id)


class ListPendingVettingUseCase:
    """OPS review queue (ADR-010): documents waiting, oldest first."""

    def __init__(self, vetting: WorkerVettingRepository) -> None:
        self._vetting = vetting

    async def execute(self, *, limit: int, offset: int) -> Sequence[PendingVettingDocument]:
        return await self._vetting.list_pending(limit=limit, offset=offset)


class ReviewIdDocumentUseCase:
    """OPS approves or rejects a worker's ID photo (ADR-010).

    Approving records the name as printed and a keyed hash of the ID number
    (never the number), which must not already verify another account.
    """

    def __init__(
        self,
        vetting: WorkerVettingRepository,
        standings: StandingRepository,
        uow: UnitOfWork,
        recompute_grade: RecomputeGradeUseCase,
        view: GetVettingViewUseCase,
        id_number_key: bytes,
    ) -> None:
        self._vetting = vetting
        self._standings = standings
        self._uow = uow
        self._recompute_grade = recompute_grade
        self._view = view
        self._key = id_number_key

    async def execute(
        self,
        *,
        worker_id: uuid.UUID,
        reviewer_id: uuid.UUID,
        approve: bool,
        verified_name: str | None,
        id_number: str | None,
        rejection_reason: str | None,
    ) -> WorkerVettingView:
        current = await self._vetting.get(worker_id)
        if current is None or current.id_photo_url is None:
            raise NotFoundError("This worker has not submitted an ID photo")
        if approve:
            name = (verified_name or "").strip()
            if not name:
                raise ValidationConflictError("Enter the name exactly as printed on the ID")
            normalized = normalize_zim_id_number(id_number or "")
            if normalized is None:
                raise ValidationConflictError(
                    "That ID number doesn't look right. Use the format 08-2047823 Q 29."
                )
            number_hash = hash_id_number(normalized, self._key)
            owner = await self._vetting.id_number_hash_owner(number_hash)
            if owner is not None and owner != worker_id:
                raise ConflictError("This ID number already verifies another account")
            await self._vetting.record_id_review(
                worker_id,
                status=VerificationStatusEnum.VERIFIED,
                reviewed_by=reviewer_id,
                reviewed_at=utcnow(),
                verified_name=name,
                id_number_hash=number_hash,
                rejection_reason=None,
            )
        else:
            reason = (rejection_reason or "").strip()
            if not reason:
                raise ValidationConflictError("Tell the worker why the ID was not accepted")
            await self._vetting.record_id_review(
                worker_id,
                status=VerificationStatusEnum.REJECTED,
                reviewed_by=reviewer_id,
                reviewed_at=utcnow(),
                verified_name=None,
                id_number_hash=None,
                rejection_reason=reason,
            )
        await self._standings.ensure(worker_id)
        await self._recompute_grade.execute(worker_id)
        try:
            await self._uow.commit()
        except IntegrityConflictError as error:
            raise ConflictError("This ID number already verifies another account") from error
        return await self._view.execute(worker_id)


class ReviewPoliceClearanceUseCase:
    """OPS approves or rejects a Police Clearance certificate (ADR-010).

    Approval needs a verified ID first (so the certificate can be matched
    against it) and an issue date; the badge lapses 12 months after issue.
    """

    def __init__(
        self,
        vetting: WorkerVettingRepository,
        uow: UnitOfWork,
        view: GetVettingViewUseCase,
    ) -> None:
        self._vetting = vetting
        self._uow = uow
        self._view = view

    async def execute(
        self,
        *,
        worker_id: uuid.UUID,
        reviewer_id: uuid.UUID,
        approve: bool,
        issued_on: date | None,
        rejection_reason: str | None,
    ) -> WorkerVettingView:
        current = await self._vetting.get(worker_id)
        if current is None or current.police_clearance_url is None:
            raise NotFoundError("This worker has not submitted a police clearance")
        today = utcnow().date()
        if approve:
            if not current.is_id_verified:
                raise ConflictError(
                    "Verify the worker's ID first, so the certificate can be matched to it"
                )
            if issued_on is None:
                raise ValidationConflictError("Enter the date the certificate was issued")
            if issued_on > today:
                raise ValidationConflictError("The issue date can't be in the future")
            expires_on = police_clearance_expiry(issued_on)
            if expires_on < today:
                raise ValidationConflictError(
                    "This certificate is more than a year old; ask the worker for a new one"
                )
            await self._vetting.record_police_clearance_review(
                worker_id,
                status=VerificationStatusEnum.VERIFIED,
                reviewed_by=reviewer_id,
                reviewed_at=utcnow(),
                issued_on=issued_on,
                expires_on=expires_on,
                rejection_reason=None,
            )
        else:
            reason = (rejection_reason or "").strip()
            if not reason:
                raise ValidationConflictError(
                    "Tell the worker why the certificate was not accepted"
                )
            await self._vetting.record_police_clearance_review(
                worker_id,
                status=VerificationStatusEnum.REJECTED,
                reviewed_by=reviewer_id,
                reviewed_at=utcnow(),
                issued_on=None,
                expires_on=None,
                rejection_reason=reason,
            )
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
        if target is None or not target.acts_as(RoleEnum.WORKER):
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


class ListNearbyWorkersUseCase:
    """List workers for the employer directory, ranked by closeness to the
    origin suburb, availability, standing grade, and completed jobs."""

    def __init__(
        self, directory: WorkerDirectoryRepository, suburbs: SuburbLookupPort
    ) -> None:
        self._directory = directory
        self._suburbs = suburbs

    async def execute(
        self,
        *,
        suburb: str | None = None,
        trade: TradeEnum | None = None,
        query: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[WorkerDirectoryItem]:
        cleaned_query = (query or "").strip()
        query_vec = embed_text(cleaned_query, trade=trade, suburb=suburb) if cleaned_query else None
        rows = await self._directory.list_workers(trade=trade, query_embedding=query_vec)
        if not rows:
            return []

        lowered_query = cleaned_query.lower()
        inferred_trade = infer_best_trade(cleaned_query)[0] if cleaned_query else None
        semantic_trades = (
            {m.trade for m in rank_skills_by_query(cleaned_query, limit=3) if m.trade is not None}
            if cleaned_query
            else set()
        )

        origin = (suburb or "").strip() or None
        suburb_names: set[str] = set()
        if origin is not None:
            suburb_names.add(origin)
            for _, areas in rows:
                for area_suburb, _ in areas:
                    suburb_names.add(area_suburb)
        coords = await self._suburbs.get_coords(suburb_names) if suburb_names else {}

        ranked: list[tuple[float, float, int, int, int, Decimal, WorkerDirectoryItem]] = []
        for item, areas in rows:
            best_band: DistanceBandEnum | None = None
            best_km: float | None = None
            best_suburb = item.suburb
            best_means = item.travel_means
            band_rank = 99

            if origin is not None and areas and origin in coords:
                best_tuple: tuple[int, float, DistanceBandEnum, str, str | None] | None = None
                for area_suburb, area_means in areas:
                    band, km = classify_distance(origin, area_suburb, coords)
                    r = BAND_RANK[band]
                    if best_tuple is None or (r, km) < (best_tuple[0], best_tuple[1]):
                        best_tuple = (r, km, band, area_suburb, area_means)
                if best_tuple is not None:
                    band_rank, raw_km, best_band, best_suburb, best_means = best_tuple
                    best_km = round(raw_km, 1)

            item.suburb = best_suburb
            item.travel_means = best_means
            item.distance_band = best_band
            item.distance_km = best_km

            sort_band = float(band_rank)
            if cleaned_query and query_vec is not None:
                profile_desc = " ".join(
                    filter(
                        None,
                        [
                            item.display_name,
                            *(t.value for t in item.trades),
                            *(area_suburb for area_suburb, _ in areas),
                        ],
                    )
                )
                profile_vec = embed_text(
                    profile_desc,
                    trade=item.trades[0] if item.trades else None,
                    suburb=item.suburb,
                )
                profile_sim = max(0.0, cosine_similarity(query_vec, profile_vec))
                db_sim = item.similarity_score or 0.0
                combined_sim = max(db_sim, profile_sim)
                final_score = relevance_score(
                    cleaned_query,
                    combined_sim,
                    description=profile_desc,
                    suburb=item.suburb,
                    trade=item.trades[0].value if item.trades else None,
                )
                name_match = lowered_query in (item.display_name or "").lower()
                suburb_match = (
                    any(lowered_query in area_suburb.lower() for area_suburb, _ in areas)
                    or lowered_query in (item.suburb or "").lower()
                )
                trade_match = (
                    any(lowered_query in t.value.lower() for t in item.trades)
                    or (inferred_trade is not None and inferred_trade in item.trades)
                    or bool(semantic_trades.intersection(item.trades))
                )
                if trade_match and final_score < 0.45:
                    final_score = 0.45
                if (name_match or suburb_match) and final_score < 0.55:
                    final_score = 0.55
                if final_score < RELEVANCE_THRESHOLD and not (
                    name_match or suburb_match or trade_match
                ):
                    continue
                item.similarity_score = round(final_score, 4)
                sort_band -= final_score * 25.0

            avail_rank = 0 if item.is_available else 1
            grade_rank = -GRADE_RANK.get(item.grade, 0)
            jobs_rank = -(item.jobs_completed or 0)
            ontime_rank = -(item.on_time_rate or _DEFAULT_ON_TIME_RATE)
            ranked.append(
                (
                    sort_band,
                    best_km if best_km is not None else 9999.0,
                    avail_rank,
                    grade_rank,
                    jobs_rank,
                    ontime_rank,
                    item,
                )
            )

        ranked.sort(key=lambda entry: entry[:6])
        return [entry[6] for entry in ranked[offset : offset + limit]]


class GetWorkerPublicProfileUseCase:
    def __init__(
        self, directory: WorkerDirectoryRepository, suburbs: SuburbLookupPort
    ) -> None:
        self._directory = directory
        self._suburbs = suburbs

    async def execute(
        self, worker_id: uuid.UUID, *, suburb: str | None = None
    ) -> WorkerPublicProfile:
        found = await self._directory.get_public_profile(worker_id)
        if found is None:
            raise NotFoundError("Worker not found")
        profile, areas = found
        origin = (suburb or "").strip() or None
        if origin is not None and areas:
            suburb_names = {origin} | {area_suburb for area_suburb, _ in areas}
            coords = await self._suburbs.get_coords(suburb_names)
            if origin in coords:
                best_tuple: tuple[int, float, DistanceBandEnum, str, str | None] | None = None
                for area_suburb, area_means in areas:
                    band, km = classify_distance(origin, area_suburb, coords)
                    r = BAND_RANK[band]
                    if best_tuple is None or (r, km) < (best_tuple[0], best_tuple[1]):
                        best_tuple = (r, km, band, area_suburb, area_means)
                if best_tuple is not None:
                    _, raw_km, best_band, best_suburb, best_means = best_tuple
                    profile.suburb = best_suburb
                    profile.travel_means = best_means
                    profile.distance_band = best_band
                    profile.distance_km = round(raw_km, 1)
        return profile

