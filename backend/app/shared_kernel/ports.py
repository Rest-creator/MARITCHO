"""Cross-app abstract interfaces (ADR-007).

Each port is declared here (rather than inside the consuming app) because
it's shared by more than one consumer/supplier pairing today. A consuming
app's domain/application code depends only on the ABC; the owning app's
infrastructure layer implements it; `main.py` (the composition root) wires
the concrete instance in.
"""

import uuid
from abc import ABC, abstractmethod
from decimal import Decimal

from app.shared_kernel.enums import TradeEnum
from app.shared_kernel.value_objects import (
    WorkerJobStats,
    WorkerServiceAreaSnapshot,
    WorkerStandingSnapshot,
)


class WorkerAvailabilityPort(ABC):
    """Whether workers are tied to an active or disputed Quick Hire job.

    Owned by the jobs app (`JobRepository` also implements this), consumed
    by: the crews app's matching service (a worker can't be assigned to a
    crew while individually busy on a Quick Hire job), and the workers
    app's standing endpoint (`is_frozen` while a job is disputed).
    """

    @abstractmethod
    async def is_worker_busy(self, worker_id: uuid.UUID) -> bool: ...

    @abstractmethod
    async def get_busy_worker_ids(self, worker_ids: set[uuid.UUID]) -> set[uuid.UUID]: ...

    @abstractmethod
    async def is_worker_disputed(self, worker_id: uuid.UUID) -> bool: ...


class WorkerJobStatsPort(ABC):
    """Aggregate Job/Dispute counts for one worker, needed to recompute
    their Standing (ADR-007). Owned by the jobs app, consumed by the
    workers app's RecomputeStandingUseCase."""

    @abstractmethod
    async def get_stats(self, worker_id: uuid.UUID) -> WorkerJobStats: ...


class WorkerMatchingProfilePort(ABC):
    """Worker-side data needed by jobs/crews matching services: which
    workers have a given skill, their declared service areas, and their
    current standing. Owned by the workers app.

    Combining these into one query per matching run was a single JOIN in
    the pre-refactor code; as separate app-boundary calls it's now several
    queries instead of one. Accepted cost of strict layering at pilot
    scale — see the already-batched (not per-candidate) busy-check
    precedent, and the dev-log's Finding #10 (Python-side matching is
    itself an already-deliberate scale trade-off).
    """

    @abstractmethod
    async def get_worker_ids_with_skill(self, trade: TradeEnum) -> set[uuid.UUID]: ...

    @abstractmethod
    async def has_skill(self, worker_id: uuid.UUID, trade: TradeEnum) -> bool: ...

    @abstractmethod
    async def get_service_areas(
        self, worker_ids: set[uuid.UUID]
    ) -> dict[uuid.UUID, list[WorkerServiceAreaSnapshot]]: ...

    @abstractmethod
    async def get_standings(
        self, worker_ids: set[uuid.UUID]
    ) -> dict[uuid.UUID, WorkerStandingSnapshot]: ...


class PaymentCollectionPort(ABC):
    """Initiate a digital collection request against a buyer, for the
    platform's booking fee (ADR-002).

    Owned by the payments app (`EcoCashGateway` implements this), consumed
    by both the jobs and crews apps' booking use cases.
    """

    @abstractmethod
    async def initiate_collection(self, *, phone: str, amount: Decimal, reference: str) -> str: ...


class SuburbLookupPort(ABC):
    """Suburb existence checks and coordinate lookups.

    Owned by the suburbs app (`SqlAlchemySuburbRepository` implements
    this), consumed by the jobs and crews apps: booking-time "does this
    suburb exist" validation, and matching-time distance-band coordinate
    lookups. Discovered as a genuine third cross-app dependency while
    building the jobs/crews matching services — not called out by name in
    the original migration plan, but the identical pattern as the other
    two ports.
    """

    @abstractmethod
    async def exists(self, name: str) -> bool: ...

    @abstractmethod
    async def get_coords(self, names: set[str]) -> dict[str, tuple[Decimal, Decimal]]: ...
