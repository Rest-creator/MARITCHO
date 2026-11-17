import uuid
from collections import defaultdict
from collections.abc import Sequence
from datetime import datetime
from decimal import Decimal

from sqlalchemy import desc, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.apps.accounts.infrastructure.models import PersonModel
from app.apps.jobs.infrastructure.models import JobModel, RecordEntryModel
from app.apps.jobs.infrastructure.review_models import ReviewModel
from app.apps.workers.domain.entities import (
    ServiceArea,
    Skill,
    Standing,
    WorkerDirectoryItem,
    WorkerPublicProfile,
    WorkerReference,
    WorkerVetting,
    WorkerVouch,
    WorkerWorkRecord,
)
from app.apps.workers.domain.repositories import (
    ServiceAreaRepository,
    SkillRepository,
    StandingRepository,
    WorkerDirectoryRepository,
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
from app.shared_kernel.enums import GradeEnum, RoleEnum, TradeEnum

_DEFAULT_ON_TIME_RATE = Decimal("100.00")
_DEFAULT_DISPUTE_RATE = Decimal("0.00")
_DEFAULT_FILL_RATE = Decimal("0.00")


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


class SqlAlchemyWorkerDirectoryRepository(WorkerDirectoryRepository):
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def list_workers(
        self,
        *,
        trade: TradeEnum | None = None,
        query_embedding: list[float] | None = None,
    ) -> list[tuple[WorkerDirectoryItem, list[tuple[str, str | None]]]]:
        if trade is not None:
            matched_ids_result = await self._db.execute(
                select(SkillModel.worker_id).where(SkillModel.trade == trade)
            )
            candidate_ids = set(matched_ids_result.scalars().all())
            if not candidate_ids:
                return []
            persons_stmt = select(PersonModel).where(
                PersonModel.role == RoleEnum.WORKER,
                PersonModel.id.in_(candidate_ids),
            )
        else:
            persons_stmt = select(PersonModel).where(PersonModel.role == RoleEnum.WORKER)

        persons_result = await self._db.execute(persons_stmt)
        persons = list(persons_result.scalars().all())
        if not persons:
            return []

        worker_ids = {person.id for person in persons}
        skills_result = await self._db.execute(
            select(SkillModel)
            .where(SkillModel.worker_id.in_(worker_ids))
            .order_by(SkillModel.id)
        )
        trades_by_worker: dict[uuid.UUID, list[TradeEnum]] = defaultdict(list)
        proofs_by_worker: dict[uuid.UUID, list[str]] = defaultdict(list)
        for skill in skills_result.scalars().all():
            if skill.trade not in trades_by_worker[skill.worker_id]:
                trades_by_worker[skill.worker_id].append(skill.trade)
            if skill.proof_url and skill.proof_url not in proofs_by_worker[skill.worker_id]:
                proofs_by_worker[skill.worker_id].append(skill.proof_url)

        skilled_persons = [person for person in persons if trades_by_worker.get(person.id)]
        if not skilled_persons:
            return []
        skilled_ids = {person.id for person in skilled_persons}

        areas_result = await self._db.execute(
            select(ServiceAreaModel)
            .where(ServiceAreaModel.worker_id.in_(skilled_ids))
            .order_by(ServiceAreaModel.id)
        )
        areas_by_worker: dict[uuid.UUID, list[tuple[str, str | None]]] = defaultdict(list)
        for area in areas_result.scalars().all():
            areas_by_worker[area.worker_id].append((area.suburb, area.travel_means))

        standings_result = await self._db.execute(
            select(StandingModel).where(StandingModel.worker_id.in_(skilled_ids))
        )
        standings_by_worker = {
            model.worker_id: model for model in standings_result.scalars().all()
        }

        ratings_result = await self._db.execute(
            select(ReviewModel.worker_id, func.avg(ReviewModel.rating), func.count())
            .where(ReviewModel.worker_id.in_(skilled_ids))
            .group_by(ReviewModel.worker_id)
        )
        ratings_by_worker: dict[uuid.UUID, tuple[Decimal | None, int]] = {
            w_id: (avg, int(cnt)) for w_id, avg, cnt in ratings_result.all()
        }

        vector_sim_by_worker: dict[uuid.UUID, float] = {}
        if query_embedding is not None:
            distance_expr = JobModel.problem_embedding.cosine_distance(query_embedding)
            sim_rows = await self._db.execute(
                select(
                    JobModel.worker_id,
                    func.max(1.0 - distance_expr).label("max_sim"),
                )
                .where(
                    JobModel.worker_id.in_(skilled_ids),
                    JobModel.problem_embedding.is_not(None),
                )
                .group_by(JobModel.worker_id)
            )
            for w_id, max_sim in sim_rows.all():
                if w_id is not None and max_sim is not None:
                    vector_sim_by_worker[w_id] = max(0.0, min(1.0, float(max_sim)))

        output: list[tuple[WorkerDirectoryItem, list[tuple[str, str | None]]]] = []
        for person in skilled_persons:
            areas = list(areas_by_worker.get(person.id, []))
            if not areas and person.home_suburb:
                areas.append((person.home_suburb, None))
            primary_suburb = areas[0][0] if areas else person.home_suburb
            primary_means = areas[0][1] if areas else None
            standing = standings_by_worker.get(person.id)
            rating_avg, rating_cnt = ratings_by_worker.get(person.id, (None, 0))
            item = WorkerDirectoryItem(
                worker_id=person.id,
                display_name=person.display_name,
                suburb=primary_suburb,
                trades=trades_by_worker[person.id],
                proof_urls=proofs_by_worker[person.id],
                grade=(standing.grade if standing and standing.grade else GradeEnum.REGISTERED),
                on_time_rate=(
                    standing.on_time_rate
                    if standing and standing.on_time_rate is not None
                    else _DEFAULT_ON_TIME_RATE
                ),
                dispute_rate=(
                    standing.dispute_rate
                    if standing and standing.dispute_rate is not None
                    else _DEFAULT_DISPUTE_RATE
                ),
                fill_rate=(
                    standing.fill_rate
                    if standing and standing.fill_rate is not None
                    else _DEFAULT_FILL_RATE
                ),
                jobs_completed=(
                    standing.jobs_completed
                    if standing and standing.jobs_completed is not None
                    else 0
                ),
                rating_average=rating_avg,
                rating_count=rating_cnt,
                is_available=person.is_available,
                travel_km=person.travel_km,
                travel_means=primary_means,
                similarity_score=vector_sim_by_worker.get(person.id),
            )
            output.append((item, areas))
        return output

    async def get_public_profile(
        self, worker_id: uuid.UUID
    ) -> tuple[WorkerPublicProfile, list[tuple[str, str | None]]] | None:
        person = await self._db.get(PersonModel, worker_id)
        if person is None or person.role != RoleEnum.WORKER:
            return None

        skills_result = await self._db.execute(
            select(SkillModel)
            .where(SkillModel.worker_id == worker_id)
            .order_by(SkillModel.id)
        )
        trades: list[TradeEnum] = []
        proof_urls: list[str] = []
        for skill in skills_result.scalars().all():
            if skill.trade not in trades:
                trades.append(skill.trade)
            if skill.proof_url and skill.proof_url not in proof_urls:
                proof_urls.append(skill.proof_url)

        areas_result = await self._db.execute(
            select(ServiceAreaModel)
            .where(ServiceAreaModel.worker_id == worker_id)
            .order_by(ServiceAreaModel.id)
        )
        areas: list[tuple[str, str | None]] = [
            (area.suburb, area.travel_means) for area in areas_result.scalars().all()
        ]
        if not areas and person.home_suburb:
            areas.append((person.home_suburb, None))

        standing = await self._db.get(StandingModel, worker_id)
        rating_row = (
            await self._db.execute(
                select(func.avg(ReviewModel.rating), func.count()).where(
                    ReviewModel.worker_id == worker_id
                )
            )
        ).one()
        rating_avg, rating_cnt = rating_row[0], int(rating_row[1] or 0)

        ref_count = (
            await self._db.scalar(
                select(func.count())
                .select_from(WorkerReferenceModel)
                .where(WorkerReferenceModel.worker_id == worker_id)
            )
            or 0
        )

        records_result = await self._db.execute(
            select(RecordEntryModel)
            .where(RecordEntryModel.worker_id == worker_id)
            .order_by(desc(RecordEntryModel.signed_off_at))
            .limit(6)
        )
        recent_work = [
            WorkerWorkRecord(
                job_id=rec.job_id,
                what_was_done=rec.what_was_done,
                client_words=rec.client_words,
                before_photo_url=rec.before_photo_url,
                after_photo_url=rec.after_photo_url,
                signed_off_at=rec.signed_off_at,
            )
            for rec in records_result.scalars().all()
        ]

        primary_suburb = areas[0][0] if areas else person.home_suburb
        primary_means = areas[0][1] if areas else None
        service_area_names = list(dict.fromkeys(suburb for suburb, _ in areas))

        profile = WorkerPublicProfile(
            worker_id=person.id,
            display_name=person.display_name,
            suburb=primary_suburb,
            trades=trades,
            proof_urls=proof_urls,
            grade=(standing.grade if standing and standing.grade else GradeEnum.REGISTERED),
            on_time_rate=(
                standing.on_time_rate
                if standing and standing.on_time_rate is not None
                else _DEFAULT_ON_TIME_RATE
            ),
            dispute_rate=(
                standing.dispute_rate
                if standing and standing.dispute_rate is not None
                else _DEFAULT_DISPUTE_RATE
            ),
            fill_rate=(
                standing.fill_rate
                if standing and standing.fill_rate is not None
                else _DEFAULT_FILL_RATE
            ),
            jobs_completed=(
                standing.jobs_completed
                if standing and standing.jobs_completed is not None
                else 0
            ),
            rating_average=rating_avg,
            rating_count=rating_cnt,
            is_available=person.is_available,
            travel_km=person.travel_km,
            travel_means=primary_means,
            service_areas=service_area_names,
            reference_count=int(ref_count),
            recent_work=recent_work,
        )
        return profile, areas

