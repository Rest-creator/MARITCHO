"""Read-only data-transfer shapes crossing a port boundary (ADR-007).

Frozen dataclasses, not full entities — used only to move data across an
app boundary via a shared_kernel port without either side importing the
other's domain module directly.
"""

from dataclasses import dataclass
from decimal import Decimal

from app.shared_kernel.enums import GradeEnum


@dataclass(frozen=True)
class WorkerStandingSnapshot:
    """Cross-app view of a worker's standing, for jobs/crews matching score
    calculations — see WorkerMatchingProfilePort."""

    grade: GradeEnum
    on_time_rate: Decimal
    dispute_rate: Decimal
    fill_rate: Decimal
    jobs_completed: int


@dataclass(frozen=True)
class WorkerServiceAreaSnapshot:
    suburb: str
    travel_means: str | None


@dataclass(frozen=True)
class WorkerJobStats:
    """Aggregate Job/Dispute counts for one worker — see WorkerJobStatsPort."""

    total_booked: int
    total_completed: int
    total_disputed: int
    total_completed_and_disputed: int
