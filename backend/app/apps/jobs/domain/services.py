import uuid
from collections.abc import Sequence
from datetime import datetime
from decimal import Decimal

from app.apps.accounts.domain.repositories import PersonRepository
from app.apps.jobs.domain.eligibility import (
    EligibilityAction,
    JobEligibility,
    audit_eligibility_denial,
    evaluate_job_eligibility,
    trade_label,
    trades_worth_scanning,
)
from app.apps.jobs.domain.entities import (
    Dispute,
    DisputeStatusEnum,
    Job,
    JobOffer,
    JobSearchResult,
    JobShareSummary,
    JobStatusEnum,
    LedgerEntry,
    MatchCandidate,
    OpenJobCandidate,
    RecordEntry,
)
from app.apps.jobs.domain.matching import JobMatchingService
from app.apps.jobs.domain.repositories import (
    DisputeRepository,
    JobOfferRepository,
    JobRepository,
    LedgerEntryRepository,
    RecordEntryRepository,
)
from app.apps.workers.domain.services import RecomputeStandingUseCase
from app.core.exceptions import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
    ValidationConflictError,
)
from app.shared_kernel.clock import utcnow
from app.shared_kernel.embeddings import (
    RELEVANCE_THRESHOLD,
    cosine_similarity,
    embed_text,
    infer_best_trade,
    relevance_score,
)
from app.shared_kernel.enums import (
    CurrencyEnum,
    DistanceBandEnum,
    LedgerEntryTypeEnum,
    NeededByEnum,
    PricingModeEnum,
    RoleEnum,
    TradeEnum,
)
from app.shared_kernel.geo import BAND_RANK, classify_distance
from app.shared_kernel.ports import (
    PaymentCollectionPort,
    SuburbLookupPort,
    WorkerMatchingProfilePort,
)
from app.shared_kernel.unit_of_work import UnitOfWork

# Offer-submitted-but-not-booked workers are only job parties while the job
# is still open for offers. Once it's BOOKED (or later), a losing bidder's
# offer row must stop granting access — only job.buyer_id/job.worker_id do.
_OFFER_GRANTS_PARTY_STATUSES = (JobStatusEnum.REQUESTED, JobStatusEnum.MATCHED)


def _require_job_party(job: Job, current_user_id: uuid.UUID, current_user_role: RoleEnum) -> None:
    is_party_to_job = current_user_id in (job.buyer_id, job.worker_id)
    if not is_party_to_job and current_user_role != RoleEnum.OPS:
        raise ForbiddenError("Not permitted to view this job")


class CreateJobRequestUseCase:
    """Ingest a Quick Hire job request (text, or a voice-note transcript arriving as text)."""

    def __init__(self, jobs: JobRepository, suburbs: SuburbLookupPort, uow: UnitOfWork) -> None:
        self._jobs = jobs
        self._suburbs = suburbs
        self._uow = uow

    async def execute(
        self,
        *,
        buyer_id: uuid.UUID,
        trade: TradeEnum,
        suburb: str,
        address: str,
        landmark_narrative: str | None,
        latitude: Decimal | None,
        longitude: Decimal | None,
        problem_description: str,
        problem_photo_url: str | None,
        budget_amount: Decimal | None = None,
        needed_by: NeededByEnum = NeededByEnum.FLEXIBLE,
        pricing_mode: PricingModeEnum = PricingModeEnum.NEGOTIABLE,
    ) -> Job:
        if not await self._suburbs.exists(suburb):
            raise ValidationConflictError("Unknown suburb")
        if pricing_mode == PricingModeEnum.FIXED and budget_amount is None:
            raise ValidationConflictError("Fixed price jobs require a budget amount")
        effective_budget = (
            None
            if pricing_mode == PricingModeEnum.AFTER_VISIT and budget_amount is None
            else budget_amount
        )

        job = await self._jobs.create(
            buyer_id=buyer_id,
            trade=trade,
            suburb=suburb,
            address=address,
            landmark_narrative=landmark_narrative,
            latitude=latitude,
            longitude=longitude,
            problem_description=problem_description,
            problem_photo_url=problem_photo_url,
            budget_amount=effective_budget,
            needed_by=needed_by,
            pricing_mode=pricing_mode,
        )
        await self._uow.commit()
        return job


class UpdateJobRequestUseCase:
    """Allow a buyer to edit their own job posting while it is still open (REQUESTED or MATCHED)."""

    def __init__(self, jobs: JobRepository, suburbs: SuburbLookupPort, uow: UnitOfWork) -> None:
        self._jobs = jobs
        self._suburbs = suburbs
        self._uow = uow

    async def execute(
        self,
        *,
        job_id: uuid.UUID,
        buyer_id: uuid.UUID,
        fields_set: set[str],
        trade: TradeEnum | None = None,
        suburb: str | None = None,
        address: str | None = None,
        landmark_narrative: str | None = None,
        latitude: Decimal | None = None,
        longitude: Decimal | None = None,
        problem_description: str | None = None,
        problem_photo_url: str | None = None,
        budget_amount: Decimal | None = None,
        needed_by: NeededByEnum | None = None,
        pricing_mode: PricingModeEnum | None = None,
    ) -> Job:
        job = await self._jobs.get(job_id)
        if job is None:
            raise NotFoundError("Job not found")
        if job.buyer_id != buyer_id:
            raise ForbiddenError("Not permitted to edit this job")
        if job.status not in (JobStatusEnum.REQUESTED, JobStatusEnum.MATCHED):
            raise ConflictError("Job can no longer be edited once a worker is booked")

        if "suburb" in fields_set:
            if suburb is None:
                raise ValidationConflictError("Suburb cannot be cleared")
            if not await self._suburbs.exists(suburb):
                raise ValidationConflictError("Unknown suburb")
            job.suburb = suburb
        if "trade" in fields_set and trade is not None:
            job.trade = trade
        if "address" in fields_set:
            if address is None:
                raise ValidationConflictError("Address cannot be cleared")
            job.address = address
        if "landmark_narrative" in fields_set:
            job.landmark_narrative = landmark_narrative
        if "latitude" in fields_set:
            job.latitude = latitude
        if "longitude" in fields_set:
            job.longitude = longitude
        if "problem_description" in fields_set:
            if problem_description is None:
                raise ValidationConflictError("Problem description cannot be cleared")
            job.problem_description = problem_description
        if "problem_photo_url" in fields_set:
            job.problem_photo_url = problem_photo_url
        if "needed_by" in fields_set and needed_by is not None:
            job.needed_by = needed_by

        pricing_mode_changed = (
            "pricing_mode" in fields_set
            and pricing_mode is not None
            and pricing_mode != job.pricing_mode
        )
        if pricing_mode_changed and pricing_mode is not None:
            job.pricing_mode = pricing_mode

        if "budget_amount" in fields_set:
            job.budget_amount = budget_amount
        elif job.pricing_mode == PricingModeEnum.AFTER_VISIT or pricing_mode_changed:
            job.budget_amount = None

        if job.pricing_mode == PricingModeEnum.FIXED and job.budget_amount is None:
            raise ValidationConflictError("Fixed price jobs require a budget amount")

        await self._jobs.save(job)
        await self._uow.commit()
        return job


class GetJobShareSummaryUseCase:
    """The public, sign-in-free teaser behind a shared job link.

    Deliberately bypasses the party check in GetJobUseCase: it returns only
    the fields in JobShareSummary, which are safe to show to anyone (job ids
    are random UUIDs, so links can't be enumerated either).
    """

    def __init__(self, jobs: JobRepository) -> None:
        self._jobs = jobs

    async def execute(self, job_id: uuid.UUID) -> JobShareSummary:
        job = await self._jobs.get(job_id)
        if job is None or job.status == JobStatusEnum.CANCELLED:
            raise NotFoundError("Job not found")
        return JobShareSummary(
            job_id=job.id,
            trade=job.trade,
            suburb=job.suburb,
            needed_by=job.needed_by,
            pricing_mode=job.pricing_mode,
            is_open=job.status in _OFFER_GRANTS_PARTY_STATUSES,
            created_at=job.created_at,
        )


class GetJobUseCase:
    def __init__(self, jobs: JobRepository, offers: JobOfferRepository | None = None) -> None:
        self._jobs = jobs
        self._offers = offers

    async def execute(
        self,
        job_id: uuid.UUID,
        current_user_id: uuid.UUID,
        current_user_capabilities: frozenset[RoleEnum],
    ) -> Job:
        job = await self._jobs.get(job_id)
        if job is None:
            raise NotFoundError("Job not found")
        is_direct_party = current_user_id in (job.buyer_id, job.worker_id)
        if not is_direct_party and RoleEnum.OPS not in current_user_capabilities:
            has_offer = False
            if (
                self._offers is not None
                and RoleEnum.WORKER in current_user_capabilities
                and job.status in _OFFER_GRANTS_PARTY_STATUSES
            ):
                job_offers = await self._offers.get_for_job(job_id)
                has_offer = current_user_id in job_offers
            if not has_offer:
                raise ForbiddenError("Not permitted to view this job")
            # Keep exact location hidden until the worker is booked (ADR-004).
            job.address = ""
            job.landmark_narrative = None
            job.latitude = None
            job.longitude = None
        return job


class ListMyJobsUseCase:
    def __init__(self, jobs: JobRepository, offers: JobOfferRepository) -> None:
        self._jobs = jobs
        self._offers = offers

    async def execute(
        self, buyer_id: uuid.UUID, *, limit: int, offset: int
    ) -> list[tuple[Job, int]]:
        jobs = await self._jobs.list_by_buyer(buyer_id, limit=limit, offset=offset)
        offer_counts = await self._offers.count_for_jobs({job.id for job in jobs})
        return [(job, offer_counts.get(job.id, 0)) for job in jobs]


class ListAssignedJobsUseCase:
    def __init__(self, jobs: JobRepository) -> None:
        self._jobs = jobs

    async def execute(self, worker_id: uuid.UUID, *, limit: int, offset: int) -> list[Job]:
        return list(await self._jobs.list_by_worker(worker_id, limit=limit, offset=offset))


class ListMyOffersUseCase:
    def __init__(self, offers: JobOfferRepository, jobs: JobRepository) -> None:
        self._offers = offers
        self._jobs = jobs

    async def execute(self, worker_id: uuid.UUID) -> list[tuple[JobOffer, Job]]:
        offers = await self._offers.list_by_worker(worker_id)
        jobs_by_id = await self._jobs.get_many({offer.job_id for offer in offers})
        return [(offer, jobs_by_id[offer.job_id]) for offer in offers if offer.job_id in jobs_by_id]


class GetJobMatchesUseCase:
    """Run the matching engine and return up to 3 ranked worker candidates.

    The first call on a REQUESTED job transitions it to MATCHED. A job past
    that lifecycle stage (BOOKED or later) no longer accepts new matches.
    """

    def __init__(
        self,
        jobs: JobRepository,
        matching: JobMatchingService,
        offers: JobOfferRepository,
        uow: UnitOfWork,
    ) -> None:
        self._jobs = jobs
        self._matching = matching
        self._offers = offers
        self._uow = uow

    async def execute(self, job_id: uuid.UUID, current_user_id: uuid.UUID) -> list[MatchCandidate]:
        job = await self._jobs.get(job_id)
        if job is None:
            raise NotFoundError("Job not found")

        if job.buyer_id != current_user_id:
            raise ForbiddenError("Not permitted to view matches for this job")

        if job.status not in (JobStatusEnum.REQUESTED, JobStatusEnum.MATCHED):
            raise ConflictError("Job is no longer accepting matches")

        offers_by_worker = await self._offers.get_for_job(job.id)
        candidates = await self._matching.find_top_candidates(
            job, priority_worker_ids=set(offers_by_worker)
        )
        for candidate in candidates:
            offer = offers_by_worker.get(candidate.worker_id)
            if offer is not None:
                candidate.quoted_amount = offer.quoted_amount
                candidate.availability_note = offer.availability_note
                candidate.quoted_at = offer.updated_at or offer.created_at

        if job.status == JobStatusEnum.REQUESTED:
            job.status = JobStatusEnum.MATCHED
            await self._jobs.save(job)
            await self._uow.commit()

        return candidates


class ListOpenJobsForWorkerUseCase:
    """Worker-facing reverse view of matching: given a worker, find jobs
    (across all of that worker's trades) they could still submit a
    JobOffer on. Mirrors JobMatchingService.find_top_candidates' distance
    loop in the opposite direction (one worker -> many jobs instead of one
    job -> many workers), reusing the same shared_kernel.geo helpers.
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

    async def execute(
        self,
        worker_id: uuid.UUID,
        *,
        limit: int,
        offset: int,
        query: str | None = None,
    ) -> list[OpenJobCandidate]:
        skills = await self._worker_profiles.get_skills_for_worker(worker_id)
        if not skills:
            return []

        areas = (await self._worker_profiles.get_service_areas({worker_id})).get(worker_id, [])
        if not areas:
            return []

        cleaned_query = (query or "").strip()
        similarity_by_job_id: dict[uuid.UUID, float] = {}
        if cleaned_query:
            query_vec = embed_text(cleaned_query)
            vector_hits = await self._jobs.search_open_by_vector(
                query_vec, trades=trades_worth_scanning(skills), limit=100
            )
            candidate_jobs = []
            for job, sim in vector_hits:
                score = relevance_score(
                    cleaned_query,
                    sim,
                    description=job.problem_description,
                    suburb=job.suburb,
                    trade=job.trade.value,
                )
                if score >= RELEVANCE_THRESHOLD:
                    candidate_jobs.append(job)
                    similarity_by_job_id[job.id] = score
        else:
            candidate_jobs = []
            for trade in trades_worth_scanning(skills):
                candidate_jobs.extend(await self._jobs.list_open_for_trade(trade))
        # Own trades always pass; catch-all jobs only when their description
        # clearly reads as one of this worker's trades (similarity search).
        candidate_jobs = [
            job
            for job in candidate_jobs
            if evaluate_job_eligibility(
                job_trade=job.trade,
                problem_description=job.problem_description or "",
                worker_skills=skills,
            ).is_eligible
        ]
        if not candidate_jobs:
            return []

        suburb_names = {job.suburb for job in candidate_jobs} | {area.suburb for area in areas}
        coords = await self._suburbs.get_coords(suburb_names)

        ranked: list[tuple[float, datetime, OpenJobCandidate]] = []
        for job in candidate_jobs:
            best: tuple[int, float, DistanceBandEnum] | None = None
            for area in areas:
                band, km = classify_distance(job.suburb, area.suburb, coords)
                rank = BAND_RANK[band]
                if best is None or (rank, km) < (best[0], best[1]):
                    best = (rank, km, band)

            assert best is not None, "areas is non-empty, so best must be set"
            band_rank, km, band = best
            if band == DistanceBandEnum.FAR:
                continue

            sim_score = similarity_by_job_id.get(job.id)
            candidate = OpenJobCandidate(
                job_id=job.id,
                trade=job.trade,
                suburb=job.suburb,
                budget_amount=job.budget_amount,
                problem_description=job.problem_description or "",
                created_at=job.created_at,
                distance_band=band,
                distance_km=round(km, 1),
                needed_by=job.needed_by,
                similarity_score=sim_score,
                pricing_mode=job.pricing_mode,
            )
            needed_value = (
                job.needed_by.value
                if isinstance(job.needed_by, NeededByEnum)
                else str(job.needed_by)
            )
            urgent_rank = {"TODAY": 0, "THIS_WEEK": 1, "FLEXIBLE": 2}.get(needed_value, 2)
            base_rank = float(urgent_rank * 10 + band_rank)
            if sim_score is not None:
                # Boost higher vector similarity first while still respecting distance/urgency
                sort_score = base_rank - (sim_score * 25.0)
            else:
                sort_score = base_rank
            ranked.append((sort_score, job.created_at or datetime.min, candidate))

        ranked.sort(key=lambda entry: (entry[0], -entry[1].timestamp()))
        return [candidate for _, _, candidate in ranked[offset : offset + limit]]


class SearchOpenJobsUseCase:
    """pgvector-powered hybrid semantic search across open jobs.

    Buyers search everything. A *worker* only ever sees jobs they're
    eligible for (see `eligibility.py`): previously a solar installer's
    search surfaced plumbing jobs they could open but never take."""

    def __init__(
        self, jobs: JobRepository, worker_profiles: WorkerMatchingProfilePort | None = None
    ) -> None:
        self._jobs = jobs
        self._worker_profiles = worker_profiles

    async def execute(
        self,
        query: str,
        *,
        trade: TradeEnum | None = None,
        suburb: str | None = None,
        limit: int = 20,
        worker_id: uuid.UUID | None = None,
    ) -> list[JobSearchResult]:
        cleaned = query.strip()
        if not cleaned:
            return []

        worker_skills: set[TradeEnum] | None = None
        if worker_id is not None and self._worker_profiles is not None:
            worker_skills = await self._worker_profiles.get_skills_for_worker(worker_id)
            scannable = trades_worth_scanning(worker_skills)
            if not scannable or (trade is not None and trade not in scannable):
                return []

        inferred_trade, _ = infer_best_trade(cleaned)
        query_vec = embed_text(cleaned, trade=trade, suburb=suburb)
        if trade is not None:
            trades_filter: list[TradeEnum] | None = [trade]
        elif worker_skills is not None:
            trades_filter = trades_worth_scanning(worker_skills)
        else:
            trades_filter = None
        rows = await self._jobs.search_open_by_vector(
            query_vec,
            trades=trades_filter,
            suburb=suburb,
            limit=limit,
        )
        results: list[JobSearchResult] = []
        for job, sim in rows:
            if (
                worker_skills is not None
                and not evaluate_job_eligibility(
                    job_trade=job.trade,
                    problem_description=job.problem_description or "",
                    worker_skills=worker_skills,
                ).is_eligible
            ):
                continue
            # Re-check direct cosine similarity as a safeguard if DB distance was 0
            if sim == 0.0 and job.problem_description:
                job_vec = embed_text(job.problem_description, trade=job.trade, suburb=job.suburb)
                sim = max(0.0, cosine_similarity(query_vec, job_vec))
            final_score = relevance_score(
                cleaned,
                sim,
                description=job.problem_description,
                suburb=job.suburb,
                trade=job.trade.value,
            )
            if final_score < RELEVANCE_THRESHOLD:
                continue
            results.append(
                JobSearchResult(
                    job_id=job.id,
                    trade=job.trade,
                    suburb=job.suburb,
                    budget_amount=job.budget_amount,
                    problem_description=job.problem_description or "",
                    created_at=job.created_at,
                    needed_by=job.needed_by,
                    similarity_score=final_score,
                    matched_trade=inferred_trade,
                    pricing_mode=job.pricing_mode,
                )
            )
        results.sort(
            key=lambda item: (
                -item.similarity_score,
                -(item.created_at.timestamp() if item.created_at else 0.0),
            )
        )
        return results[:limit]


class CheckJobEligibilityUseCase:
    """Can this worker see and offer on this job? Lets the app explain a
    mismatch ("this job needs plumbing…") instead of a dead end, and audits
    every denied look."""

    def __init__(self, jobs: JobRepository, worker_profiles: WorkerMatchingProfilePort) -> None:
        self._jobs = jobs
        self._worker_profiles = worker_profiles

    async def execute(self, *, job_id: uuid.UUID, worker_id: uuid.UUID) -> JobEligibility:
        job = await self._jobs.get(job_id)
        if job is None:
            raise NotFoundError("Job not found")
        skills = await self._worker_profiles.get_skills_for_worker(worker_id)
        eligibility = evaluate_job_eligibility(
            job_trade=job.trade,
            problem_description=job.problem_description or "",
            worker_skills=skills,
        )
        if not eligibility.is_eligible:
            audit_eligibility_denial(
                action=EligibilityAction.VIEW,
                worker_id=worker_id,
                job_id=job_id,
                eligibility=eligibility,
                worker_skills=skills,
            )
        return eligibility


class SubmitJobOfferUseCase:
    """A worker (not yet booked) attaches their own price + availability to
    a job that's still open (REQUESTED/MATCHED) — the hybrid matching
    extension. Resubmitting revises the existing offer (upsert)."""

    def __init__(
        self,
        jobs: JobRepository,
        worker_profiles: WorkerMatchingProfilePort,
        offers: JobOfferRepository,
        uow: UnitOfWork,
    ) -> None:
        self._jobs = jobs
        self._worker_profiles = worker_profiles
        self._offers = offers
        self._uow = uow

    async def execute(
        self,
        *,
        job_id: uuid.UUID,
        worker_id: uuid.UUID,
        quoted_amount: Decimal,
        availability_note: str | None,
    ) -> JobOffer:
        job = await self._jobs.get(job_id)
        if job is None:
            raise NotFoundError("Job not found")

        if job.status not in (JobStatusEnum.REQUESTED, JobStatusEnum.MATCHED):
            raise ConflictError("Job is no longer open for offers")

        skills = await self._worker_profiles.get_skills_for_worker(worker_id)
        eligibility = evaluate_job_eligibility(
            job_trade=job.trade,
            problem_description=job.problem_description or "",
            worker_skills=skills,
        )
        if not eligibility.is_eligible:
            audit_eligibility_denial(
                action=EligibilityAction.OFFER,
                worker_id=worker_id,
                job_id=job_id,
                eligibility=eligibility,
                worker_skills=skills,
            )
            raise ValidationConflictError(eligibility.reason)

        if await self._jobs.is_worker_busy(worker_id):
            raise ConflictError("You are already committed to another active job")

        offer = await self._offers.upsert(
            job_id=job_id,
            worker_id=worker_id,
            quoted_amount=quoted_amount,
            availability_note=availability_note,
        )
        await self._uow.commit()
        return offer


class BookJobUseCase:
    """Book a worker for a matched job: holds the deposit and reveals the address.

    The chosen worker must be a registered WORKER with a skill in this
    job's trade and not already tied to another active job.
    """

    def __init__(
        self,
        jobs: JobRepository,
        persons: PersonRepository,
        worker_profiles: WorkerMatchingProfilePort,
        ledger: LedgerEntryRepository,
        payment_gateway: PaymentCollectionPort,
        uow: UnitOfWork,
    ) -> None:
        self._jobs = jobs
        self._persons = persons
        self._worker_profiles = worker_profiles
        self._ledger = ledger
        self._payment_gateway = payment_gateway
        self._uow = uow

    async def execute(
        self,
        *,
        job_id: uuid.UUID,
        buyer_id: uuid.UUID,
        buyer_phone: str,
        worker_id: uuid.UUID,
        deposit_amount: Decimal,
        currency: CurrencyEnum,
    ) -> Job:
        job = await self._jobs.get(job_id)
        if job is None:
            raise NotFoundError("Job not found")

        if job.buyer_id != buyer_id:
            raise ForbiddenError("Not permitted to book this job")

        if job.status != JobStatusEnum.MATCHED:
            raise ConflictError("Job must be MATCHED before it can be booked")

        worker = await self._persons.get_by_id(worker_id)
        # Capability, not mode: someone who also hires can still be booked.
        if worker is None or not worker.acts_as(RoleEnum.WORKER):
            raise ValidationConflictError("worker_id does not refer to a registered worker")

        skills = await self._worker_profiles.get_skills_for_worker(worker_id)
        eligibility = evaluate_job_eligibility(
            job_trade=job.trade,
            problem_description=job.problem_description or "",
            worker_skills=skills,
        )
        if not eligibility.is_eligible:
            audit_eligibility_denial(
                action=EligibilityAction.BOOK,
                worker_id=worker_id,
                job_id=job_id,
                eligibility=eligibility,
                worker_skills=skills,
            )
            raise ValidationConflictError(
                f"This worker doesn't list {trade_label(job.trade)} among their skills. "
                "Choose a worker who does."
            )

        if await self._jobs.is_worker_busy(worker_id):
            raise ConflictError("Worker is already committed to another active job")

        external_reference = None
        if currency == CurrencyEnum.ECOCASH:
            external_reference = await self._payment_gateway.initiate_collection(
                phone=buyer_phone,
                amount=deposit_amount,
                reference=str(job.id),
            )

        job.worker_id = worker_id
        job.status = JobStatusEnum.BOOKED
        job.currency = currency
        await self._jobs.save(job)
        await self._ledger.add(
            job_id=job.id,
            amount=deposit_amount,
            entry_type=LedgerEntryTypeEnum.DEPOSIT_HELD,
            currency=currency,
            external_reference=external_reference,
        )
        await self._uow.commit()
        return job


class SubmitQuoteUseCase:
    """The assigned worker submits their on-site price assessment.

    Commits the remaining balance (quote minus the deposit already held)
    and moves the job into IN_PROGRESS.
    """

    def __init__(self, jobs: JobRepository, ledger: LedgerEntryRepository, uow: UnitOfWork) -> None:
        self._jobs = jobs
        self._ledger = ledger
        self._uow = uow

    async def execute(
        self,
        *,
        job_id: uuid.UUID,
        worker_id: uuid.UUID,
        labor_amount: Decimal,
        materials_amount: Decimal,
    ) -> Job:
        job = await self._jobs.get(job_id)
        if job is None:
            raise NotFoundError("Job not found")

        if job.worker_id != worker_id:
            raise ForbiddenError("Not permitted to submit a quote for this job")

        if job.status != JobStatusEnum.BOOKED:
            raise ConflictError("Job must be BOOKED before a quote can be submitted")

        quote_amount = labor_amount + materials_amount
        deposit_total = await self._ledger.sum_by_type(job.id, LedgerEntryTypeEnum.DEPOSIT_HELD)
        if quote_amount <= deposit_total:
            raise ValidationConflictError("Quote must exceed the deposit already held")

        assert job.currency is not None, "BOOKED implies a currency was set"
        job.labor_amount = labor_amount
        job.materials_amount = materials_amount
        job.quote_amount = quote_amount
        job.status = JobStatusEnum.IN_PROGRESS
        await self._jobs.save(job)
        await self._ledger.add(
            job_id=job.id,
            amount=quote_amount - deposit_total,
            entry_type=LedgerEntryTypeEnum.BALANCE_COMMITTED,
            currency=job.currency,
        )
        await self._uow.commit()
        return job


class CompleteJobUseCase:
    """Buyer signs off: writes the immutable record entry and releases the balance."""

    def __init__(
        self,
        jobs: JobRepository,
        records: RecordEntryRepository,
        ledger: LedgerEntryRepository,
        recompute_standing: RecomputeStandingUseCase,
        uow: UnitOfWork,
    ) -> None:
        self._jobs = jobs
        self._records = records
        self._ledger = ledger
        self._recompute_standing = recompute_standing
        self._uow = uow

    async def execute(
        self,
        *,
        job_id: uuid.UUID,
        buyer_id: uuid.UUID,
        what_was_done: str,
        client_words: str | None,
        before_photo_url: str | None,
        after_photo_url: str | None,
    ) -> Job:
        job = await self._jobs.get(job_id)
        if job is None:
            raise NotFoundError("Job not found")

        if job.buyer_id != buyer_id:
            raise ForbiddenError("Not permitted to complete this job")

        if job.status != JobStatusEnum.IN_PROGRESS:
            raise ConflictError("Job must be IN_PROGRESS before it can be completed")

        assert job.worker_id is not None, "IN_PROGRESS implies a booked worker"
        await self._records.add(
            job_id=job.id,
            worker_id=job.worker_id,
            what_was_done=what_was_done,
            client_words=client_words,
            before_photo_url=before_photo_url,
            after_photo_url=after_photo_url,
            signed_off_at=utcnow(),
        )
        assert job.currency is not None, "IN_PROGRESS implies a currency was set"
        assert job.quote_amount is not None, "IN_PROGRESS implies a quote was submitted"
        await self._ledger.add(
            job_id=job.id,
            amount=job.quote_amount,
            entry_type=LedgerEntryTypeEnum.RELEASED,
            currency=job.currency,
        )
        job.status = JobStatusEnum.COMPLETED
        await self._jobs.save(job)
        await self._recompute_standing.execute(job.worker_id)
        await self._uow.commit()
        return job


class RaiseDisputeUseCase:
    """Buyer raises a concern: money freezes (no further ledger release) and
    the job moves to DISPUTED. The worker must answer before any consequence."""

    def __init__(
        self,
        jobs: JobRepository,
        disputes: DisputeRepository,
        recompute_standing: RecomputeStandingUseCase,
        uow: UnitOfWork,
    ) -> None:
        self._jobs = jobs
        self._disputes = disputes
        self._recompute_standing = recompute_standing
        self._uow = uow

    async def execute(self, *, job_id: uuid.UUID, buyer_id: uuid.UUID, reason: str) -> Dispute:
        job = await self._jobs.get(job_id)
        if job is None:
            raise NotFoundError("Job not found")

        if job.buyer_id != buyer_id:
            raise ForbiddenError("Not permitted to dispute this job")

        if job.status != JobStatusEnum.IN_PROGRESS:
            raise ConflictError("Job must be IN_PROGRESS before it can be disputed")

        dispute = await self._disputes.add(job_id=job.id, raised_by_id=buyer_id, reason=reason)
        job.status = JobStatusEnum.DISPUTED
        await self._jobs.save(job)
        assert job.worker_id is not None, "IN_PROGRESS implies a booked worker"
        await self._recompute_standing.execute(job.worker_id)
        await self._uow.commit()
        return dispute


class RespondToDisputeUseCase:
    """Assigned worker answers the dispute. Standing was frozen, not dropped,
    while it was open. Default outcome is a return visit, not a refund."""

    def __init__(self, jobs: JobRepository, disputes: DisputeRepository, uow: UnitOfWork) -> None:
        self._jobs = jobs
        self._disputes = disputes
        self._uow = uow

    async def execute(
        self,
        *,
        job_id: uuid.UUID,
        worker_id: uuid.UUID,
        response: str,
        before_photo_url: str | None,
        after_photo_url: str | None,
    ) -> Dispute:
        job = await self._jobs.get(job_id)
        if job is None:
            raise NotFoundError("Job not found")

        if job.worker_id != worker_id:
            raise ForbiddenError("Not permitted to respond to this dispute")

        if job.status != JobStatusEnum.DISPUTED:
            raise ConflictError("Job is not currently disputed")

        dispute = await self._disputes.get_latest_open(job.id)
        if dispute is None:
            raise NotFoundError("No open dispute for this job")

        dispute.worker_response = response
        dispute.before_photo_url = before_photo_url
        dispute.after_photo_url = after_photo_url
        dispute.status = DisputeStatusEnum.RESOLVED_RETURN_VISIT
        dispute.responded_at = utcnow()
        await self._disputes.save(dispute)

        job.status = JobStatusEnum.IN_PROGRESS
        await self._jobs.save(job)

        await self._uow.commit()
        return dispute


class ListJobDisputesUseCase:
    def __init__(self, jobs: JobRepository, disputes: DisputeRepository) -> None:
        self._jobs = jobs
        self._disputes = disputes

    async def execute(
        self,
        job_id: uuid.UUID,
        current_user_id: uuid.UUID,
        current_user_role: RoleEnum,
        *,
        limit: int,
        offset: int,
    ) -> Sequence[Dispute]:
        job = await self._jobs.get(job_id)
        if job is None:
            raise NotFoundError("Job not found")
        _require_job_party(job, current_user_id, current_user_role)
        return await self._disputes.list_by_job(job_id, limit=limit, offset=offset)


class GetJobLedgerUseCase:
    def __init__(self, jobs: JobRepository, ledger: LedgerEntryRepository) -> None:
        self._jobs = jobs
        self._ledger = ledger

    async def execute(
        self,
        job_id: uuid.UUID,
        current_user_id: uuid.UUID,
        current_user_role: RoleEnum,
        *,
        limit: int,
        offset: int,
    ) -> Sequence[LedgerEntry]:
        job = await self._jobs.get(job_id)
        if job is None:
            raise NotFoundError("Job not found")
        _require_job_party(job, current_user_id, current_user_role)
        return await self._ledger.list_by_job(job_id, limit=limit, offset=offset)


class GetJobRecordUseCase:
    def __init__(self, jobs: JobRepository, records: RecordEntryRepository) -> None:
        self._jobs = jobs
        self._records = records

    async def execute(
        self, job_id: uuid.UUID, current_user_id: uuid.UUID, current_user_role: RoleEnum
    ) -> RecordEntry:
        job = await self._jobs.get(job_id)
        if job is None:
            raise NotFoundError("Job not found")
        _require_job_party(job, current_user_id, current_user_role)

        record = await self._records.get_by_job(job_id)
        if record is None:
            raise NotFoundError("No record entry yet")
        return record
