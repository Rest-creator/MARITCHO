import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.apps.jobs.domain.entities import JobStatusEnum
from app.apps.jobs.infrastructure.models import DisputeModel, JobModel
from app.shared_kernel.ports import WorkerJobStatsPort
from app.shared_kernel.value_objects import WorkerJobStats


class WorkerJobStatsAdapter(WorkerJobStatsPort):
    """Aggregates Job/Dispute counts for RecomputeStandingUseCase (owned by
    the workers app) — moved from app/standing.py::recompute_standing's
    query block, minus the Standing read/write, which stays in workers."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_stats(self, worker_id: uuid.UUID) -> WorkerJobStats:
        total_booked = await self._db.scalar(
            select(func.count()).select_from(JobModel).where(JobModel.worker_id == worker_id)
        )
        total_completed = await self._db.scalar(
            select(func.count())
            .select_from(JobModel)
            .where(JobModel.worker_id == worker_id, JobModel.status == JobStatusEnum.COMPLETED)
        )
        total_disputed = await self._db.scalar(
            select(func.count(func.distinct(JobModel.id)))
            .select_from(JobModel)
            .join(DisputeModel, DisputeModel.job_id == JobModel.id)
            .where(JobModel.worker_id == worker_id)
        )
        total_completed_and_disputed = await self._db.scalar(
            select(func.count(func.distinct(JobModel.id)))
            .select_from(JobModel)
            .join(DisputeModel, DisputeModel.job_id == JobModel.id)
            .where(JobModel.worker_id == worker_id, JobModel.status == JobStatusEnum.COMPLETED)
        )

        return WorkerJobStats(
            total_booked=total_booked or 0,
            total_completed=total_completed or 0,
            total_disputed=total_disputed or 0,
            total_completed_and_disputed=total_completed_and_disputed or 0,
        )
