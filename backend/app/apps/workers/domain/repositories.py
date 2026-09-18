import uuid
from abc import ABC, abstractmethod
from collections.abc import Sequence
from datetime import datetime

from app.apps.workers.domain.entities import (
    ServiceArea,
    Skill,
    Standing,
    WorkerReference,
    WorkerVetting,
    WorkerVouch,
)
from app.shared_kernel.enums import GradeEnum, TradeEnum


class SkillRepository(ABC):
    @abstractmethod
    async def add(self, *, worker_id: uuid.UUID, trade: TradeEnum, proof_url: str | None) -> Skill:
        """Flushes (populating id); raises IntegrityConflictError on a
        duplicate (worker_id, trade). Does not commit."""

    @abstractmethod
    async def list_by_worker(
        self, worker_id: uuid.UUID, *, limit: int, offset: int
    ) -> Sequence[Skill]: ...


class ServiceAreaRepository(ABC):
    @abstractmethod
    async def add(
        self, *, worker_id: uuid.UUID, suburb: str, travel_means: str | None
    ) -> ServiceArea:
        """Flushes; raises IntegrityConflictError on a duplicate
        (worker_id, suburb). Does not commit."""

    @abstractmethod
    async def list_by_worker(
        self, worker_id: uuid.UUID, *, limit: int, offset: int
    ) -> Sequence[ServiceArea]: ...


class StandingRepository(ABC):
    @abstractmethod
    async def get(self, worker_id: uuid.UUID) -> Standing | None: ...

    @abstractmethod
    async def ensure(self, worker_id: uuid.UUID) -> None:
        """Creates a Standing row (with defaults) if none exists yet.
        Stages only — does not commit."""

    @abstractmethod
    async def save(self, standing: Standing) -> None:
        """Persists mutated grade/rate fields for an existing row. Stages
        only — does not commit."""


class WorkerVettingRepository(ABC):
    @abstractmethod
    async def get(self, worker_id: uuid.UUID) -> WorkerVetting | None: ...

    @abstractmethod
    async def upsert_id_photo(
        self, worker_id: uuid.UUID, id_photo_url: str, submitted_at: datetime
    ) -> WorkerVetting:
        """Stages only — does not commit."""


class WorkerReferenceRepository(ABC):
    @abstractmethod
    async def add(self, *, worker_id: uuid.UUID, name: str, phone: str) -> WorkerReference:
        """Flushes (populating id). Does not commit."""

    @abstractmethod
    async def list_by_worker(
        self, worker_id: uuid.UUID, *, limit: int, offset: int
    ) -> Sequence[WorkerReference]: ...

    @abstractmethod
    async def count_by_worker(self, worker_id: uuid.UUID) -> int: ...


class WorkerVouchRepository(ABC):
    @abstractmethod
    async def add(self, *, worker_id: uuid.UUID, voucher_id: uuid.UUID) -> WorkerVouch:
        """Flushes (populating id); raises IntegrityConflictError on a
        duplicate (worker_id, voucher_id) or a self-vouch. Does not commit."""

    @abstractmethod
    async def count_by_worker(self, worker_id: uuid.UUID) -> int: ...

    @abstractmethod
    async def count_valid_vouches(
        self, worker_id: uuid.UUID, qualifying_grades: set[GradeEnum]
    ) -> int:
        """Counts vouches where the *current* voucher grade is one of
        `qualifying_grades`."""
