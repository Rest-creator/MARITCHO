import uuid
from abc import ABC, abstractmethod
from collections.abc import Sequence
from datetime import date, datetime

from app.apps.workers.domain.entities import (
    PendingVettingDocument,
    ServiceArea,
    Skill,
    Standing,
    WorkerDirectoryItem,
    WorkerPublicProfile,
    WorkerReference,
    WorkerVetting,
    WorkerVouch,
)
from app.shared_kernel.enums import GradeEnum, TradeEnum, VerificationStatusEnum


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

    @abstractmethod
    async def upsert_police_clearance(
        self, worker_id: uuid.UUID, police_clearance_url: str, submitted_at: datetime
    ) -> WorkerVetting:
        """Stages only — does not commit."""

    @abstractmethod
    async def record_id_review(
        self,
        worker_id: uuid.UUID,
        *,
        status: VerificationStatusEnum,
        reviewed_by: uuid.UUID,
        reviewed_at: datetime,
        verified_name: str | None,
        id_number_hash: str | None,
        rejection_reason: str | None,
    ) -> WorkerVetting:
        """Stages only — does not commit. A duplicate id_number_hash surfaces
        as IntegrityConflictError on commit."""

    @abstractmethod
    async def record_police_clearance_review(
        self,
        worker_id: uuid.UUID,
        *,
        status: VerificationStatusEnum,
        reviewed_by: uuid.UUID,
        reviewed_at: datetime,
        issued_on: date | None,
        expires_on: date | None,
        rejection_reason: str | None,
    ) -> WorkerVetting:
        """Stages only — does not commit."""

    @abstractmethod
    async def id_number_hash_owner(self, id_number_hash: str) -> uuid.UUID | None:
        """The worker whose verified ID already has this number, if any."""

    @abstractmethod
    async def list_pending(self, *, limit: int, offset: int) -> Sequence[PendingVettingDocument]:
        """Documents waiting for review, oldest submission first."""


class MediaOwnershipRepository(ABC):
    """Port onto the media store, so vetting only accepts real uploads."""

    @abstractmethod
    async def is_owned_image(self, media_id: uuid.UUID, owner_id: uuid.UUID) -> bool: ...


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


class WorkerDirectoryRepository(ABC):
    @abstractmethod
    async def list_workers(
        self,
        *,
        trade: TradeEnum | None = None,
        query_embedding: list[float] | None = None,
    ) -> list[tuple[WorkerDirectoryItem, list[tuple[str, str | None]]]]:
        """Returns (WorkerDirectoryItem, [(suburb, travel_means), ...]) for
        all registered workers who have at least one skill."""

    @abstractmethod
    async def get_public_profile(
        self, worker_id: uuid.UUID
    ) -> tuple[WorkerPublicProfile, list[tuple[str, str | None]]] | None:
        """Returns the public profile and service areas for `worker_id`, or
        None if not found."""

