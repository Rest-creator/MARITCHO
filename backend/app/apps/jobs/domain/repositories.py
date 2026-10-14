import uuid
from abc import ABC, abstractmethod
from collections.abc import Sequence
from datetime import datetime
from decimal import Decimal

from app.apps.jobs.domain.entities import Dispute, Job, JobOffer, LedgerEntry, RecordEntry
from app.shared_kernel.enums import CurrencyEnum, LedgerEntryTypeEnum, NeededByEnum, TradeEnum


class JobRepository(ABC):
    @abstractmethod
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
        budget_amount: Decimal | None,
        needed_by: NeededByEnum = NeededByEnum.FLEXIBLE,
    ) -> Job:
        """Flushes (populating id/timestamps). Does not commit."""

    @abstractmethod
    async def get(self, job_id: uuid.UUID) -> Job | None: ...

    @abstractmethod
    async def save(self, job: Job) -> None:
        """Persists mutated fields for an existing row. Flushes only — does not commit."""

    @abstractmethod
    async def is_worker_busy(self, worker_id: uuid.UUID) -> bool:
        """True if this worker is tied to another active (non-terminal) job."""

    @abstractmethod
    async def get_busy_worker_ids(self, worker_ids: set[uuid.UUID]) -> set[uuid.UUID]:
        """Batched form of is_worker_busy, to avoid N+1 checks over a candidate pool."""

    @abstractmethod
    async def is_worker_disputed(self, worker_id: uuid.UUID) -> bool:
        """True if this worker has any job currently under an open dispute."""

    @abstractmethod
    async def list_open_for_trade(self, trade: TradeEnum) -> Sequence[Job]:
        """Jobs in REQUESTED/MATCHED status for this trade — candidates a
        worker could still submit a JobOffer on. Ordered by created_at
        desc. No pagination param: realistic pilot-scale volume, same
        trade-off already accepted for the Python-side matching engine."""

    @abstractmethod
    async def list_by_buyer(self, buyer_id: uuid.UUID, *, limit: int, offset: int) -> Sequence[Job]:
        """This buyer's own jobs, newest first — user-facing and
        potentially unbounded, unlike list_open_for_trade, so real
        pagination applies here."""

    @abstractmethod
    async def list_by_worker(
        self, worker_id: uuid.UUID, *, limit: int, offset: int
    ) -> Sequence[Job]:
        """This worker's own jobs (any status), newest first — same
        pagination reasoning as list_by_buyer."""

    @abstractmethod
    async def get_many(self, job_ids: set[uuid.UUID]) -> dict[uuid.UUID, Job]:
        """Batched job lookup, keyed by id — avoids N+1 when enriching a
        worker's offer list with job context."""


class LedgerEntryRepository(ABC):
    @abstractmethod
    async def add(
        self,
        *,
        job_id: uuid.UUID,
        amount: Decimal,
        entry_type: LedgerEntryTypeEnum,
        currency: CurrencyEnum,
        external_reference: str | None = None,
    ) -> LedgerEntry:
        """Flushes (populating id). Does not commit. ledger_entries is
        insert-only at the DB level (trigger blocks UPDATE/DELETE)."""

    @abstractmethod
    async def sum_by_type(self, job_id: uuid.UUID, entry_type: LedgerEntryTypeEnum) -> Decimal: ...

    @abstractmethod
    async def list_by_job(
        self, job_id: uuid.UUID, *, limit: int, offset: int
    ) -> Sequence[LedgerEntry]: ...


class DisputeRepository(ABC):
    @abstractmethod
    async def add(self, *, job_id: uuid.UUID, raised_by_id: uuid.UUID, reason: str) -> Dispute:
        """Flushes (populating id). Does not commit."""

    @abstractmethod
    async def get_latest_open(self, job_id: uuid.UUID) -> Dispute | None: ...

    @abstractmethod
    async def save(self, dispute: Dispute) -> None:
        """Persists mutated fields for an existing row. Flushes only — does not commit."""

    @abstractmethod
    async def list_by_job(
        self, job_id: uuid.UUID, *, limit: int, offset: int
    ) -> Sequence[Dispute]: ...


class RecordEntryRepository(ABC):
    @abstractmethod
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
        """Flushes (populating id). Does not commit."""

    @abstractmethod
    async def get_by_job(self, job_id: uuid.UUID) -> RecordEntry | None: ...


class JobOfferRepository(ABC):
    @abstractmethod
    async def upsert(
        self,
        *,
        job_id: uuid.UUID,
        worker_id: uuid.UUID,
        quoted_amount: Decimal,
        availability_note: str | None,
    ) -> JobOffer:
        """Creates or revises the (job_id, worker_id) offer. Flushes only — does not commit."""

    @abstractmethod
    async def get(self, job_id: uuid.UUID, worker_id: uuid.UUID) -> JobOffer | None: ...

    @abstractmethod
    async def get_for_job(self, job_id: uuid.UUID) -> dict[uuid.UUID, JobOffer]:
        """Batched lookup, keyed by worker_id — avoids N+1 when enriching
        up to 3 ranked match candidates."""

    @abstractmethod
    async def count_for_jobs(self, job_ids: set[uuid.UUID]) -> dict[uuid.UUID, int]:
        """Batched offer count, keyed by job_id — avoids N+1 when listing
        a buyer's own jobs."""

    @abstractmethod
    async def list_by_worker(self, worker_id: uuid.UUID) -> Sequence[JobOffer]:
        """This worker's own submitted offers, across all jobs. No
        pagination param: a single worker's offer count is inherently
        small, same trade-off as list_open_for_trade."""
