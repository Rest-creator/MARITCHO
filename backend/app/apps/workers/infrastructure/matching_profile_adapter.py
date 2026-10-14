import uuid
from collections import defaultdict
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.apps.accounts.infrastructure.models import PersonModel
from app.apps.jobs.infrastructure.review_models import ReviewModel
from app.apps.workers.infrastructure.models import ServiceAreaModel, SkillModel, StandingModel
from app.shared_kernel.enums import GradeEnum, TradeEnum
from app.shared_kernel.ports import WorkerMatchingProfilePort
from app.shared_kernel.value_objects import (
    WorkerProfileSnapshot,
    WorkerServiceAreaSnapshot,
    WorkerStandingSnapshot,
)

_DEFAULT_ON_TIME_RATE = Decimal("100.00")
_DEFAULT_DISPUTE_RATE = Decimal("0.00")
_DEFAULT_FILL_RATE = Decimal("0.00")


class WorkerMatchingProfileAdapter(WorkerMatchingProfilePort):
    """Implements the cross-app matching-data port directly against the
    workers app's own ORM models — a dedicated adapter rather than
    composing the narrower SkillRepository/ServiceAreaRepository/
    StandingRepository, so jobs/crews matching gets efficient batched
    queries instead of N+1 round-trips (ADR-007)."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_worker_ids_with_skill(self, trade: TradeEnum) -> set[uuid.UUID]:
        result = await self._db.execute(
            select(SkillModel.worker_id).where(SkillModel.trade == trade)
        )
        return set(result.scalars().all())

    async def has_skill(self, worker_id: uuid.UUID, trade: TradeEnum) -> bool:
        result = await self._db.execute(
            select(SkillModel.id)
            .where(SkillModel.worker_id == worker_id, SkillModel.trade == trade)
            .limit(1)
        )
        return result.first() is not None

    async def get_skills_for_worker(self, worker_id: uuid.UUID) -> set[TradeEnum]:
        result = await self._db.execute(
            select(SkillModel.trade).where(SkillModel.worker_id == worker_id)
        )
        return set(result.scalars().all())

    async def get_service_areas(
        self, worker_ids: set[uuid.UUID]
    ) -> dict[uuid.UUID, list[WorkerServiceAreaSnapshot]]:
        if not worker_ids:
            return {}
        result = await self._db.execute(
            select(ServiceAreaModel).where(ServiceAreaModel.worker_id.in_(worker_ids))
        )
        areas_by_worker: dict[uuid.UUID, list[WorkerServiceAreaSnapshot]] = defaultdict(list)
        for model in result.scalars().all():
            areas_by_worker[model.worker_id].append(
                WorkerServiceAreaSnapshot(suburb=model.suburb, travel_means=model.travel_means)
            )
        people = await self._db.execute(
            select(PersonModel.id, PersonModel.home_suburb).where(PersonModel.id.in_(worker_ids))
        )
        for worker_id, home_suburb in people.all():
            if home_suburb and worker_id not in areas_by_worker:
                areas_by_worker[worker_id].append(
                    WorkerServiceAreaSnapshot(suburb=home_suburb, travel_means=None)
                )
        return dict(areas_by_worker)

    async def get_standings(
        self, worker_ids: set[uuid.UUID]
    ) -> dict[uuid.UUID, WorkerStandingSnapshot]:
        if not worker_ids:
            return {}
        result = await self._db.execute(
            select(StandingModel).where(StandingModel.worker_id.in_(worker_ids))
        )
        snapshots: dict[uuid.UUID, WorkerStandingSnapshot] = {}
        for model in result.scalars().all():
            snapshots[model.worker_id] = WorkerStandingSnapshot(
                grade=model.grade or GradeEnum.REGISTERED,
                on_time_rate=(
                    model.on_time_rate if model.on_time_rate is not None else _DEFAULT_ON_TIME_RATE
                ),
                dispute_rate=(
                    model.dispute_rate if model.dispute_rate is not None else _DEFAULT_DISPUTE_RATE
                ),
                fill_rate=model.fill_rate if model.fill_rate is not None else _DEFAULT_FILL_RATE,
                jobs_completed=model.jobs_completed if model.jobs_completed is not None else 0,
            )
        ratings = await self._db.execute(
            select(ReviewModel.worker_id, func.avg(ReviewModel.rating), func.count())
            .where(ReviewModel.worker_id.in_(worker_ids))
            .group_by(ReviewModel.worker_id)
        )
        for worker_id, average, count in ratings.all():
            current = snapshots.get(worker_id)
            if current:
                snapshots[worker_id] = WorkerStandingSnapshot(
                    grade=current.grade,
                    on_time_rate=current.on_time_rate,
                    dispute_rate=current.dispute_rate,
                    fill_rate=current.fill_rate,
                    jobs_completed=current.jobs_completed,
                    rating_average=average,
                    rating_count=count,
                )
            else:
                snapshots[worker_id] = WorkerStandingSnapshot(
                    grade=GradeEnum.REGISTERED,
                    on_time_rate=_DEFAULT_ON_TIME_RATE,
                    dispute_rate=_DEFAULT_DISPUTE_RATE,
                    fill_rate=_DEFAULT_FILL_RATE,
                    jobs_completed=0,
                    rating_average=average,
                    rating_count=count,
                )
        return snapshots

    async def get_profiles(
        self, worker_ids: set[uuid.UUID]
    ) -> dict[uuid.UUID, WorkerProfileSnapshot]:
        if not worker_ids:
            return {}
        result = await self._db.execute(select(PersonModel).where(PersonModel.id.in_(worker_ids)))
        return {
            model.id: WorkerProfileSnapshot(
                display_name=model.display_name,
                is_available=model.is_available,
                travel_km=model.travel_km,
                home_suburb=model.home_suburb,
            )
            for model in result.scalars().all()
        }
