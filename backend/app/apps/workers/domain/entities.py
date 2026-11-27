import uuid
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal

from app.shared_kernel.enums import (
    DistanceBandEnum,
    GradeEnum,
    TradeEnum,
    VerificationStatusEnum,
)


@dataclass
class Skill:
    id: uuid.UUID
    worker_id: uuid.UUID
    trade: TradeEnum
    grade: GradeEnum | None = None
    proof_url: str | None = None


@dataclass
class ServiceArea:
    id: uuid.UUID
    worker_id: uuid.UUID
    suburb: str
    travel_means: str | None = None


@dataclass
class Standing:
    """Computed, never assigned (per the PRD) — see RecomputeStandingUseCase
    and RecomputeGradeUseCase, the only two writers of the mutable fields."""

    worker_id: uuid.UUID
    grade: GradeEnum | None = GradeEnum.REGISTERED
    on_time_rate: Decimal | None = Decimal("100.00")
    dispute_rate: Decimal | None = Decimal("0.00")
    fill_rate: Decimal | None = Decimal("0.00")
    jobs_completed: int | None = 0


@dataclass
class StandingView:
    """Standing plus the computed (never stored) is_frozen flag, returned
    to the router — matches the shape GET /workers/me/standing returns."""

    worker_id: uuid.UUID
    grade: GradeEnum
    on_time_rate: Decimal
    dispute_rate: Decimal
    fill_rate: Decimal
    jobs_completed: int
    is_frozen: bool
    rating_average: Decimal | None = None
    rating_count: int = 0


@dataclass
class WorkerVetting:
    """Identity documents (ADR-005, ADR-010). The photos are private: only the
    worker and OPS can open them. Badges follow the review status, never the
    mere presence of a photo."""

    worker_id: uuid.UUID
    id_photo_url: str | None = None
    id_submitted_at: datetime | None = None
    police_clearance_url: str | None = None
    police_clearance_submitted_at: datetime | None = None
    id_status: VerificationStatusEnum | None = None
    id_reviewed_at: datetime | None = None
    id_reviewed_by: uuid.UUID | None = None
    id_rejection_reason: str | None = None
    id_verified_name: str | None = None
    police_clearance_status: VerificationStatusEnum | None = None
    police_clearance_reviewed_at: datetime | None = None
    police_clearance_reviewed_by: uuid.UUID | None = None
    police_clearance_rejection_reason: str | None = None
    police_clearance_issued_on: date | None = None
    police_clearance_expires_on: date | None = None

    @property
    def is_id_verified(self) -> bool:
        return self.id_status == VerificationStatusEnum.VERIFIED

    def is_police_cleared(self, today: date) -> bool:
        return is_police_clearance_current(
            self.police_clearance_status, self.police_clearance_expires_on, today
        )


def is_police_clearance_current(
    status: VerificationStatusEnum | None, expires_on: date | None, today: date
) -> bool:
    """The "Police Cleared" badge: reviewed, approved and not yet expired."""
    return (
        status == VerificationStatusEnum.VERIFIED
        and expires_on is not None
        and expires_on >= today
    )


@dataclass
class PendingVettingDocument:
    """One document waiting in the OPS review queue."""

    worker_id: uuid.UUID
    worker_name: str | None
    worker_phone: str
    document: str  # "ID" | "POLICE_CLEARANCE"
    photo_url: str
    submitted_at: datetime | None
    id_status: VerificationStatusEnum | None
    id_verified_name: str | None


@dataclass
class WorkerReference:
    id: uuid.UUID
    worker_id: uuid.UUID
    name: str
    phone: str
    created_at: datetime | None = None


@dataclass
class WorkerVouch:
    id: uuid.UUID
    worker_id: uuid.UUID
    voucher_id: uuid.UUID
    created_at: datetime | None = None


@dataclass
class WorkerVettingView:
    """Evidence + computed grade, returned by GET /workers/me/vetting and
    every vetting-mutation endpoint."""

    worker_id: uuid.UUID
    id_photo_url: str | None
    id_submitted_at: datetime | None
    reference_count: int
    vouch_count: int
    grade: GradeEnum
    police_clearance_url: str | None = None
    police_clearance_submitted_at: datetime | None = None
    id_status: VerificationStatusEnum | None = None
    id_rejection_reason: str | None = None
    id_verified_name: str | None = None
    police_clearance_status: VerificationStatusEnum | None = None
    police_clearance_rejection_reason: str | None = None
    police_clearance_issued_on: date | None = None
    police_clearance_expires_on: date | None = None
    has_police_clearance: bool = False


@dataclass
class WorkerWorkRecord:
    job_id: uuid.UUID
    what_was_done: str
    client_words: str | None = None
    before_photo_url: str | None = None
    after_photo_url: str | None = None
    signed_off_at: datetime | None = None


@dataclass
class WorkerDirectoryItem:
    worker_id: uuid.UUID
    display_name: str | None
    suburb: str | None
    trades: list[TradeEnum]
    proof_urls: list[str]
    grade: GradeEnum
    on_time_rate: Decimal
    dispute_rate: Decimal
    fill_rate: Decimal
    jobs_completed: int
    rating_average: Decimal | None = None
    rating_count: int = 0
    is_available: bool = True
    travel_km: int = 50
    travel_means: str | None = None
    distance_band: DistanceBandEnum | None = None
    distance_km: float | None = None
    similarity_score: float | None = None
    has_police_clearance: bool = False


@dataclass
class WorkerPublicProfile(WorkerDirectoryItem):
    service_areas: list[str] | None = None
    reference_count: int = 0
    recent_work: list[WorkerWorkRecord] | None = None

