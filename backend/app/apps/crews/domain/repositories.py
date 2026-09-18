import uuid
from abc import ABC, abstractmethod
from collections.abc import Sequence
from decimal import Decimal

from app.apps.crews.domain.entities import Crew, CrewMember, CrewOrder, CrewOrderLedgerEntry
from app.shared_kernel.enums import CurrencyEnum, LedgerEntryTypeEnum, TradeEnum


class CrewRepository(ABC):
    @abstractmethod
    async def create(self, *, lead_id: uuid.UUID, name: str | None) -> Crew:
        """Flushes (populating id); raises IntegrityConflictError if this
        lead already has a crew (unique lead_id). Does not commit."""

    @abstractmethod
    async def get(self, crew_id: uuid.UUID) -> Crew | None: ...

    @abstractmethod
    async def get_by_lead(self, lead_id: uuid.UUID) -> Crew | None: ...

    @abstractmethod
    async def list_all(self) -> Sequence[Crew]: ...


class CrewMemberRepository(ABC):
    @abstractmethod
    async def add(self, *, crew_id: uuid.UUID, worker_id: uuid.UUID) -> CrewMember:
        """Flushes; raises IntegrityConflictError on a duplicate
        (crew_id, worker_id). Does not commit."""

    @abstractmethod
    async def get(self, crew_id: uuid.UUID, worker_id: uuid.UUID) -> CrewMember | None: ...

    @abstractmethod
    async def remove(self, member: CrewMember) -> None:
        """Deletes the row. Stages only — does not commit."""

    @abstractmethod
    async def list_worker_ids_by_crew(self, crew_id: uuid.UUID) -> list[uuid.UUID]: ...

    @abstractmethod
    async def list_worker_ids_by_crews(
        self, crew_ids: Sequence[uuid.UUID]
    ) -> dict[uuid.UUID, list[uuid.UUID]]:
        """Batched form of list_worker_ids_by_crew, for matching."""


class CrewOrderRepository(ABC):
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
        workers_needed: int,
        problem_description: str | None,
    ) -> CrewOrder:
        """Flushes (populating id/timestamps). Does not commit."""

    @abstractmethod
    async def get(self, order_id: uuid.UUID) -> CrewOrder | None: ...

    @abstractmethod
    async def save(self, order: CrewOrder) -> None:
        """Persists mutated fields for an existing row. Flushes only — does not commit."""

    @abstractmethod
    async def is_crew_busy(self, crew_id: uuid.UUID) -> bool: ...

    @abstractmethod
    async def get_busy_crew_ids(self, crew_ids: Sequence[uuid.UUID]) -> set[uuid.UUID]:
        """Batched form of is_crew_busy, to avoid N+1 checks over a candidate pool."""


class CrewOrderLedgerEntryRepository(ABC):
    @abstractmethod
    async def add(
        self,
        *,
        crew_order_id: uuid.UUID,
        amount: Decimal,
        entry_type: LedgerEntryTypeEnum,
        currency: CurrencyEnum,
        external_reference: str | None = None,
    ) -> CrewOrderLedgerEntry:
        """Flushes (populating id). Does not commit. crew_order_ledger_entries
        is insert-only at the DB level (trigger blocks UPDATE/DELETE)."""

    @abstractmethod
    async def sum_by_type(
        self, crew_order_id: uuid.UUID, entry_type: LedgerEntryTypeEnum
    ) -> Decimal: ...

    @abstractmethod
    async def list_by_crew_order(
        self, crew_order_id: uuid.UUID, *, limit: int, offset: int
    ) -> Sequence[CrewOrderLedgerEntry]: ...
