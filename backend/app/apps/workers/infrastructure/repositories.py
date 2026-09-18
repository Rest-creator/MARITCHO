import uuid
from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.apps.workers.domain.entities import (
    ServiceArea,
    Skill,
    Standing,
    WorkerReference,
    WorkerVetting,
    WorkerVouch,
)
from app.apps.workers.domain.repositories import (
    ServiceAreaRepository,
    SkillRepository,
    StandingRepository,
    WorkerReferenceRepository,
    WorkerVettingRepository,
    WorkerVouchRepository,
)
from app.apps.workers.infrastructure.models import (
    ServiceAreaModel,
    SkillModel,
    StandingModel,
    WorkerReferenceModel,
    WorkerVettingModel,
    WorkerVouchModel,
)
from app.core.exceptions import IntegrityConflictError
from app.shared_kernel.enums import GradeEnum, TradeEnum


def _skill_to_entity(model: SkillModel) -> Skill:
    return Skill(
        id=model.id, worker_id=model.worker_id, trade=model.trade,
        grade=model.grade, proof_url=model.proof_url,
    )


def _service_area_to_entity(model: ServiceAreaModel) -> ServiceArea:
    return ServiceArea(
        id=model.id, worker_id=model.worker_id, suburb=model.suburb,
        travel_means=model.travel_means,
    )


def _standing_to_entity(model: StandingModel) -> Standing:
    return Standing(
        worker_id=model.worker_id, grade=model.grade, on_time_rate=model.on_time_rate,
        dispute_rate=model.dispute_rate, fill_rate=model.fill_rate,
        jobs_completed=model.jobs_completed,
    )


def _vetting_to_entity(model: WorkerVettingModel) -> WorkerVetting:
    return WorkerVetting(
        worker_id=model.worker_id, id_photo_url=model.id_photo_url,
        id_submitted_at=model.id_submitted_at,
    )


def _reference_to_entity(model: WorkerReferenceModel) -> WorkerReference:
    return WorkerReference(
        id=model.id, worker_id=model.worker_id, name=model.name, phone=model.phone,
        created_at=model.created_at,
    )


def _vouch_to_entity(model: WorkerVouchModel) -> WorkerVouch:
    return WorkerVouch(
        id=model.id, worker_id=model.worker_id, voucher_id=model.voucher_id,
        created_at=model.created_at,
    )


class SqlAlchemySkillRepository(SkillRepository):
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def add(self, *, worker_id: uuid.UUID, trade: TradeEnum, proof_url: str | None) -> Skill:
        model = SkillModel(worker_id=worker_id, trade=trade, proof_url=proof_url)
        self._db.add(model)
        try:
            await self._db.flush()
        except IntegrityError as exc:
            await self._db.rollback()
            raise IntegrityConflictError(str(exc)) from exc
        return _skill_to_entity(model)

    async def list_by_worker(
        self, worker_id: uuid.UUID, *, limit: int, offset: int
    ) -> Sequence[Skill]:
        result = await self._db.execute(
            select(SkillModel)
            .where(SkillModel.worker_id == worker_id)
            .order_by(SkillModel.id)
            .limit(limit)
            .offset(offset)
        )
        return [_skill_to_entity(model) for model in result.scalars().all()]


class SqlAlchemyServiceAreaRepository(ServiceAreaRepository):
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def add(
        self, *, worker_id: uuid.UUID, suburb: str, travel_means: str | None
    ) -> ServiceArea:
        model = ServiceAreaModel(worker_id=worker_id, suburb=suburb, travel_means=travel_means)
        self._db.add(model)
        try:
            await self._db.flush()
        except IntegrityError as exc:
            await self._db.rollback()
            raise IntegrityConflictError(str(exc)) from exc
        return _service_area_to_entity(model)

    async def list_by_worker(
        self, worker_id: uuid.UUID, *, limit: int, offset: int
    ) -> Sequence[ServiceArea]:
        result = await self._db.execute(
            select(ServiceAreaModel)
            .where(ServiceAreaModel.worker_id == worker_id)
            .order_by(ServiceAreaModel.id)
            .limit(limit)
            .offset(offset)
        )
        return [_service_area_to_entity(model) for model in result.scalars().all()]


class SqlAlchemyStandingRepository(StandingRepository):
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get(self, worker_id: uuid.UUID) -> Standing | None:
        model = await self._db.get(StandingModel, worker_id)
        return _standing_to_entity(model) if model else None

    async def ensure(self, worker_id: uuid.UUID) -> None:
        model = await self._db.get(StandingModel, worker_id)
        if model is None:
            self._db.add(StandingModel(worker_id=worker_id))

    async def save(self, standing: Standing) -> None:
        model = await self._db.get(StandingModel, standing.worker_id)
        if model is None:
            return
        model.grade = standing.grade
        model.on_time_rate = standing.on_time_rate
        model.dispute_rate = standing.dispute_rate
        model.fill_rate = standing.fill_rate
        model.jobs_completed = standing.jobs_completed
        await self._db.flush()


class SqlAlchemyWorkerVettingRepository(WorkerVettingRepository):
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get(self, worker_id: uuid.UUID) -> WorkerVetting | None:
        model = await self._db.get(WorkerVettingModel, worker_id)
        return _vetting_to_entity(model) if model else None

    async def upsert_id_photo(
        self, worker_id: uuid.UUID, id_photo_url: str, submitted_at: datetime
    ) -> WorkerVetting:
        model = await self._db.get(WorkerVettingModel, worker_id)
        if model is None:
            model = WorkerVettingModel(worker_id=worker_id)
            self._db.add(model)
        model.id_photo_url = id_photo_url
        model.id_submitted_at = submitted_at
        await self._db.flush()
        return _vetting_to_entity(model)


class SqlAlchemyWorkerReferenceRepository(WorkerReferenceRepository):
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def add(self, *, worker_id: uuid.UUID, name: str, phone: str) -> WorkerReference:
        model = WorkerReferenceModel(worker_id=worker_id, name=name, phone=phone)
        self._db.add(model)
        await self._db.flush()
        return _reference_to_entity(model)

    async def list_by_worker(
        self, worker_id: uuid.UUID, *, limit: int, offset: int
    ) -> Sequence[WorkerReference]:
        result = await self._db.execute(
            select(WorkerReferenceModel)
            .where(WorkerReferenceModel.worker_id == worker_id)
            .order_by(WorkerReferenceModel.created_at)
            .limit(limit)
            .offset(offset)
        )
        return [_reference_to_entity(model) for model in result.scalars().all()]

    async def count_by_worker(self, worker_id: uuid.UUID) -> int:
        return (
            await self._db.scalar(
                select(func.count())
                .select_from(WorkerReferenceModel)
                .where(WorkerReferenceModel.worker_id == worker_id)
            )
            or 0
        )


class SqlAlchemyWorkerVouchRepository(WorkerVouchRepository):
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def add(self, *, worker_id: uuid.UUID, voucher_id: uuid.UUID) -> WorkerVouch:
        model = WorkerVouchModel(worker_id=worker_id, voucher_id=voucher_id)
        self._db.add(model)
        try:
            await self._db.flush()
        except IntegrityError as exc:
            await self._db.rollback()
            raise IntegrityConflictError(str(exc)) from exc
        return _vouch_to_entity(model)

    async def count_by_worker(self, worker_id: uuid.UUID) -> int:
        return (
            await self._db.scalar(
                select(func.count())
                .select_from(WorkerVouchModel)
                .where(WorkerVouchModel.worker_id == worker_id)
            )
            or 0
        )

    async def count_valid_vouches(
        self, worker_id: uuid.UUID, qualifying_grades: set[GradeEnum]
    ) -> int:
        return (
            await self._db.scalar(
                select(func.count())
                .select_from(WorkerVouchModel)
                .join(StandingModel, StandingModel.worker_id == WorkerVouchModel.voucher_id)
                .where(
                    WorkerVouchModel.worker_id == worker_id,
                    StandingModel.grade.in_(qualifying_grades),
                )
            )
            or 0
        )
