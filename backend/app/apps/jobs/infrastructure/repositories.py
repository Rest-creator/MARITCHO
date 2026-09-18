import uuid
from collections.abc import Sequence
from datetime import datetime
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.apps.jobs.domain.entities import (
    JOB_BUSY_STATUSES,
    Dispute,
    DisputeStatusEnum,
    Job,
    JobStatusEnum,
    LedgerEntry,
    RecordEntry,
)
from app.apps.jobs.domain.repositories import (
    DisputeRepository,
    JobRepository,
    LedgerEntryRepository,
    RecordEntryRepository,
)
from app.apps.jobs.infrastructure.models import (
    DisputeModel,
    JobModel,
    LedgerEntryModel,
    RecordEntryModel,
)
from app.shared_kernel.enums import CurrencyEnum, LedgerEntryTypeEnum, TradeEnum
from app.shared_kernel.ports import WorkerAvailabilityPort


def _job_to_entity(model: JobModel) -> Job:
    return Job(
        id=model.id,
        buyer_id=model.buyer_id,
        worker_id=model.worker_id,
        status=model.status,
        trade=model.trade,
        suburb=model.suburb,
        address=model.address,
        landmark_narrative=model.landmark_narrative,
        latitude=model.latitude,
        longitude=model.longitude,
        problem_description=model.problem_description,
        problem_photo_url=model.problem_photo_url,
        currency=model.currency,
        labor_amount=model.labor_amount,
        materials_amount=model.materials_amount,
        quote_amount=model.quote_amount,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def _ledger_entry_to_entity(model: LedgerEntryModel) -> LedgerEntry:
    return LedgerEntry(
        id=model.id,
        job_id=model.job_id,
        amount=model.amount,
        entry_type=model.entry_type,
        currency=model.currency,
        external_reference=model.external_reference,
        created_at=model.created_at,
    )


def _dispute_to_entity(model: DisputeModel) -> Dispute:
    return Dispute(
        id=model.id,
        job_id=model.job_id,
        raised_by_id=model.raised_by_id,
        reason=model.reason,
        status=model.status,
        worker_response=model.worker_response,
        before_photo_url=model.before_photo_url,
        after_photo_url=model.after_photo_url,
        created_at=model.created_at,
        responded_at=model.responded_at,
    )


def _record_entry_to_entity(model: RecordEntryModel) -> RecordEntry:
    return RecordEntry(
        id=model.id,
        job_id=model.job_id,
        worker_id=model.worker_id,
        what_was_done=model.what_was_done,
        client_words=model.client_words,
        before_photo_url=model.before_photo_url,
        after_photo_url=model.after_photo_url,
        signed_off_at=model.signed_off_at,
    )


class SqlAlchemyJobRepository(JobRepository, WorkerAvailabilityPort):
    """Implements both the app's own repository interface and the
    shared_kernel WorkerAvailabilityPort other apps consume (ADR-007)."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(
        self,
        *,
        buyer_id: uuid.UUID,
        trade: TradeEnum,
        suburb: str,
        address: str,
        landmark_narrative: str | None,
        latitude: Decimal | None,
        longitude: Decimal | None,
        problem_description: str | None,
        problem_photo_url: str | None,
    ) -> Job:
        model = JobModel(
            buyer_id=buyer_id,
            status=JobStatusEnum.REQUESTED,
            trade=trade,
            suburb=suburb,
            address=address,
            landmark_narrative=landmark_narrative,
            latitude=latitude,
            longitude=longitude,
            problem_description=problem_description,
            problem_photo_url=problem_photo_url,
        )
        self._db.add(model)
        await self._db.flush()
        await self._db.refresh(model)
        return _job_to_entity(model)

    async def get(self, job_id: uuid.UUID) -> Job | None:
        model = await self._db.get(JobModel, job_id)
        return _job_to_entity(model) if model else None

    async def save(self, job: Job) -> None:
        model = await self._db.get(JobModel, job.id)
        if model is None:
            return
        model.worker_id = job.worker_id
        model.status = job.status
        model.currency = job.currency
        model.labor_amount = job.labor_amount
        model.materials_amount = job.materials_amount
        model.quote_amount = job.quote_amount
        await self._db.flush()

    async def is_worker_busy(self, worker_id: uuid.UUID) -> bool:
        result = await self._db.execute(
            select(JobModel.id)
            .where(JobModel.worker_id == worker_id, JobModel.status.in_(JOB_BUSY_STATUSES))
            .limit(1)
        )
        return result.first() is not None

    async def get_busy_worker_ids(self, worker_ids: set[uuid.UUID]) -> set[uuid.UUID]:
        if not worker_ids:
            return set()
        result = await self._db.execute(
            select(JobModel.worker_id.distinct()).where(
                JobModel.worker_id.in_(worker_ids), JobModel.status.in_(JOB_BUSY_STATUSES)
            )
        )
        return {worker_id for worker_id in result.scalars().all() if worker_id is not None}

    async def is_worker_disputed(self, worker_id: uuid.UUID) -> bool:
        result = await self._db.execute(
            select(JobModel.id)
            .where(JobModel.worker_id == worker_id, JobModel.status == JobStatusEnum.DISPUTED)
            .limit(1)
        )
        return result.first() is not None


class SqlAlchemyLedgerEntryRepository(LedgerEntryRepository):
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def add(
        self,
        *,
        job_id: uuid.UUID,
        amount: Decimal,
        entry_type: LedgerEntryTypeEnum,
        currency: CurrencyEnum,
        external_reference: str | None = None,
    ) -> LedgerEntry:
        model = LedgerEntryModel(
            job_id=job_id,
            amount=amount,
            entry_type=entry_type,
            currency=currency,
            external_reference=external_reference,
        )
        self._db.add(model)
        await self._db.flush()
        return _ledger_entry_to_entity(model)

    async def sum_by_type(self, job_id: uuid.UUID, entry_type: LedgerEntryTypeEnum) -> Decimal:
        result = await self._db.execute(
            select(func.coalesce(func.sum(LedgerEntryModel.amount), 0)).where(
                LedgerEntryModel.job_id == job_id, LedgerEntryModel.entry_type == entry_type
            )
        )
        return result.scalar_one()

    async def list_by_job(
        self, job_id: uuid.UUID, *, limit: int, offset: int
    ) -> Sequence[LedgerEntry]:
        result = await self._db.execute(
            select(LedgerEntryModel)
            .where(LedgerEntryModel.job_id == job_id)
            .order_by(LedgerEntryModel.created_at)
            .limit(limit)
            .offset(offset)
        )
        return [_ledger_entry_to_entity(model) for model in result.scalars().all()]


class SqlAlchemyDisputeRepository(DisputeRepository):
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def add(self, *, job_id: uuid.UUID, raised_by_id: uuid.UUID, reason: str) -> Dispute:
        model = DisputeModel(
            job_id=job_id,
            raised_by_id=raised_by_id,
            reason=reason,
            status=DisputeStatusEnum.OPEN,
        )
        self._db.add(model)
        await self._db.flush()
        return _dispute_to_entity(model)

    async def get_latest_open(self, job_id: uuid.UUID) -> Dispute | None:
        result = await self._db.execute(
            select(DisputeModel)
            .where(DisputeModel.job_id == job_id, DisputeModel.status == DisputeStatusEnum.OPEN)
            .order_by(DisputeModel.created_at.desc())
        )
        model = result.scalars().first()
        return _dispute_to_entity(model) if model else None

    async def save(self, dispute: Dispute) -> None:
        model = await self._db.get(DisputeModel, dispute.id)
        if model is None:
            return
        model.worker_response = dispute.worker_response
        model.before_photo_url = dispute.before_photo_url
        model.after_photo_url = dispute.after_photo_url
        model.status = dispute.status
        model.responded_at = dispute.responded_at
        await self._db.flush()

    async def list_by_job(
        self, job_id: uuid.UUID, *, limit: int, offset: int
    ) -> Sequence[Dispute]:
        result = await self._db.execute(
            select(DisputeModel)
            .where(DisputeModel.job_id == job_id)
            .order_by(DisputeModel.created_at)
            .limit(limit)
            .offset(offset)
        )
        return [_dispute_to_entity(model) for model in result.scalars().all()]


class SqlAlchemyRecordEntryRepository(RecordEntryRepository):
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def add(
        self,
        *,
        job_id: uuid.UUID,
        worker_id: uuid.UUID,
        what_was_done: str,
        client_words: str | None,
        before_photo_url: str | None,
        after_photo_url: str | None,
        signed_off_at: datetime,
    ) -> RecordEntry:
        model = RecordEntryModel(
            job_id=job_id,
            worker_id=worker_id,
            what_was_done=what_was_done,
            client_words=client_words,
            before_photo_url=before_photo_url,
            after_photo_url=after_photo_url,
            signed_off_at=signed_off_at,
        )
        self._db.add(model)
        await self._db.flush()
        return _record_entry_to_entity(model)

    async def get_by_job(self, job_id: uuid.UUID) -> RecordEntry | None:
        result = await self._db.execute(
            select(RecordEntryModel).where(RecordEntryModel.job_id == job_id)
        )
        model = result.scalars().first()
        return _record_entry_to_entity(model) if model else None
