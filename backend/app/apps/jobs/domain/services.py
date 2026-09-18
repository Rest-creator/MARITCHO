import uuid
from collections.abc import Sequence
from datetime import datetime
from decimal import Decimal

from app.apps.accounts.domain.repositories import PersonRepository
from app.apps.jobs.domain.entities import (
    Dispute,
    DisputeStatusEnum,
    Job,
    JobStatusEnum,
    LedgerEntry,
    MatchCandidate,
    RecordEntry,
)
from app.apps.jobs.domain.matching import JobMatchingService
from app.apps.jobs.domain.repositories import (
    DisputeRepository,
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
from app.shared_kernel.enums import CurrencyEnum, LedgerEntryTypeEnum, RoleEnum, TradeEnum
from app.shared_kernel.ports import (
    PaymentCollectionPort,
    SuburbLookupPort,
    WorkerMatchingProfilePort,
)
from app.shared_kernel.unit_of_work import UnitOfWork


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
    ) -> Job:
        if not await self._suburbs.exists(suburb):
            raise ValidationConflictError("Unknown suburb")

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
        )
        await self._uow.commit()
        return job


class GetJobUseCase:
    def __init__(self, jobs: JobRepository) -> None:
        self._jobs = jobs

    async def execute(
        self, job_id: uuid.UUID, current_user_id: uuid.UUID, current_user_role: RoleEnum
    ) -> Job:
        job = await self._jobs.get(job_id)
        if job is None:
            raise NotFoundError("Job not found")
        _require_job_party(job, current_user_id, current_user_role)
        return job


class GetJobMatchesUseCase:
    """Run the matching engine and return up to 3 ranked worker candidates.

    The first call on a REQUESTED job transitions it to MATCHED. A job past
    that lifecycle stage (BOOKED or later) no longer accepts new matches.
    """

    def __init__(self, jobs: JobRepository, matching: JobMatchingService, uow: UnitOfWork) -> None:
        self._jobs = jobs
        self._matching = matching
        self._uow = uow

    async def execute(self, job_id: uuid.UUID, current_user_id: uuid.UUID) -> list[MatchCandidate]:
        job = await self._jobs.get(job_id)
        if job is None:
            raise NotFoundError("Job not found")

        if job.buyer_id != current_user_id:
            raise ForbiddenError("Not permitted to view matches for this job")

        if job.status not in (JobStatusEnum.REQUESTED, JobStatusEnum.MATCHED):
            raise ConflictError("Job is no longer accepting matches")

        candidates = await self._matching.find_top_candidates(job)

        if job.status == JobStatusEnum.REQUESTED:
            job.status = JobStatusEnum.MATCHED
            await self._jobs.save(job)
            await self._uow.commit()

        return candidates


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
        if worker is None or worker.role != RoleEnum.WORKER:
            raise ValidationConflictError("worker_id does not refer to a registered worker")

        if not await self._worker_profiles.has_skill(worker_id, job.trade):
            raise ValidationConflictError("Worker is not skilled in this job's trade")

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
            signed_off_at=datetime.utcnow(),
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
        dispute.responded_at = datetime.utcnow()
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
