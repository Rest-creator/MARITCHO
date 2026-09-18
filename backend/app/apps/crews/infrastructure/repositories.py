import uuid
from collections import defaultdict
from collections.abc import Sequence
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.apps.crews.domain.entities import (
    CREW_BUSY_STATUSES,
    Crew,
    CrewMember,
    CrewOrder,
    CrewOrderLedgerEntry,
    CrewOrderStatusEnum,
)
from app.apps.crews.domain.repositories import (
    CrewMemberRepository,
    CrewOrderLedgerEntryRepository,
    CrewOrderRepository,
    CrewRepository,
)
from app.apps.crews.infrastructure.models import (
    CrewMemberModel,
    CrewModel,
    CrewOrderLedgerEntryModel,
    CrewOrderModel,
)
from app.core.exceptions import IntegrityConflictError
from app.shared_kernel.enums import CurrencyEnum, LedgerEntryTypeEnum, TradeEnum


def _crew_to_entity(model: CrewModel) -> Crew:
    return Crew(id=model.id, lead_id=model.lead_id, name=model.name)


def _crew_member_to_entity(model: CrewMemberModel) -> CrewMember:
    return CrewMember(crew_id=model.crew_id, worker_id=model.worker_id)


def _crew_order_to_entity(model: CrewOrderModel) -> CrewOrder:
    return CrewOrder(
        id=model.id,
        buyer_id=model.buyer_id,
        crew_id=model.crew_id,
        status=model.status,
        trade=model.trade,
        suburb=model.suburb,
        address=model.address,
        landmark_narrative=model.landmark_narrative,
        latitude=model.latitude,
        longitude=model.longitude,
        workers_needed=model.workers_needed,
        problem_description=model.problem_description,
        currency=model.currency,
        labor_amount=model.labor_amount,
        materials_amount=model.materials_amount,
        quote_amount=model.quote_amount,
        completion_note=model.completion_note,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def _crew_order_ledger_entry_to_entity(model: CrewOrderLedgerEntryModel) -> CrewOrderLedgerEntry:
    return CrewOrderLedgerEntry(
        id=model.id,
        crew_order_id=model.crew_order_id,
        amount=model.amount,
        entry_type=model.entry_type,
        currency=model.currency,
        external_reference=model.external_reference,
        created_at=model.created_at,
    )


class SqlAlchemyCrewRepository(CrewRepository):
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(self, *, lead_id: uuid.UUID, name: str | None) -> Crew:
        model = CrewModel(lead_id=lead_id, name=name)
        self._db.add(model)
        try:
            await self._db.flush()
        except IntegrityError as exc:
            await self._db.rollback()
            raise IntegrityConflictError(str(exc)) from exc
        return _crew_to_entity(model)

    async def get(self, crew_id: uuid.UUID) -> Crew | None:
        model = await self._db.get(CrewModel, crew_id)
        return _crew_to_entity(model) if model else None

    async def get_by_lead(self, lead_id: uuid.UUID) -> Crew | None:
        result = await self._db.execute(select(CrewModel).where(CrewModel.lead_id == lead_id))
        model = result.scalars().first()
        return _crew_to_entity(model) if model else None

    async def list_all(self) -> Sequence[Crew]:
        result = await self._db.execute(select(CrewModel))
        return [_crew_to_entity(model) for model in result.scalars().all()]


class SqlAlchemyCrewMemberRepository(CrewMemberRepository):
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def add(self, *, crew_id: uuid.UUID, worker_id: uuid.UUID) -> CrewMember:
        model = CrewMemberModel(crew_id=crew_id, worker_id=worker_id)
        self._db.add(model)
        try:
            await self._db.flush()
        except IntegrityError as exc:
            await self._db.rollback()
            raise IntegrityConflictError(str(exc)) from exc
        return _crew_member_to_entity(model)

    async def get(self, crew_id: uuid.UUID, worker_id: uuid.UUID) -> CrewMember | None:
        model = await self._db.get(CrewMemberModel, {"crew_id": crew_id, "worker_id": worker_id})
        return _crew_member_to_entity(model) if model else None

    async def remove(self, member: CrewMember) -> None:
        model = await self._db.get(
            CrewMemberModel, {"crew_id": member.crew_id, "worker_id": member.worker_id}
        )
        if model is None:
            return
        await self._db.delete(model)
        await self._db.flush()

    async def list_worker_ids_by_crew(self, crew_id: uuid.UUID) -> list[uuid.UUID]:
        result = await self._db.execute(
            select(CrewMemberModel.worker_id).where(CrewMemberModel.crew_id == crew_id)
        )
        return list(result.scalars().all())

    async def list_worker_ids_by_crews(
        self, crew_ids: Sequence[uuid.UUID]
    ) -> dict[uuid.UUID, list[uuid.UUID]]:
        if not crew_ids:
            return {}
        result = await self._db.execute(
            select(CrewMemberModel).where(CrewMemberModel.crew_id.in_(crew_ids))
        )
        worker_ids_by_crew: dict[uuid.UUID, list[uuid.UUID]] = defaultdict(list)
        for model in result.scalars().all():
            worker_ids_by_crew[model.crew_id].append(model.worker_id)
        return dict(worker_ids_by_crew)


class SqlAlchemyCrewOrderRepository(CrewOrderRepository):
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

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
        model = CrewOrderModel(
            buyer_id=buyer_id,
            status=CrewOrderStatusEnum.REQUESTED,
            trade=trade,
            suburb=suburb,
            address=address,
            landmark_narrative=landmark_narrative,
            latitude=latitude,
            longitude=longitude,
            workers_needed=workers_needed,
            problem_description=problem_description,
        )
        self._db.add(model)
        await self._db.flush()
        await self._db.refresh(model)
        return _crew_order_to_entity(model)

    async def get(self, order_id: uuid.UUID) -> CrewOrder | None:
        model = await self._db.get(CrewOrderModel, order_id)
        return _crew_order_to_entity(model) if model else None

    async def save(self, order: CrewOrder) -> None:
        model = await self._db.get(CrewOrderModel, order.id)
        if model is None:
            return
        model.crew_id = order.crew_id
        model.status = order.status
        model.currency = order.currency
        model.labor_amount = order.labor_amount
        model.materials_amount = order.materials_amount
        model.quote_amount = order.quote_amount
        model.completion_note = order.completion_note
        await self._db.flush()

    async def is_crew_busy(self, crew_id: uuid.UUID) -> bool:
        result = await self._db.execute(
            select(CrewOrderModel.id)
            .where(CrewOrderModel.crew_id == crew_id, CrewOrderModel.status.in_(CREW_BUSY_STATUSES))
            .limit(1)
        )
        return result.first() is not None

    async def get_busy_crew_ids(self, crew_ids: Sequence[uuid.UUID]) -> set[uuid.UUID]:
        if not crew_ids:
            return set()
        result = await self._db.execute(
            select(CrewOrderModel.crew_id.distinct()).where(
                CrewOrderModel.crew_id.in_(crew_ids), CrewOrderModel.status.in_(CREW_BUSY_STATUSES)
            )
        )
        return {crew_id for crew_id in result.scalars().all() if crew_id is not None}


class SqlAlchemyCrewOrderLedgerEntryRepository(CrewOrderLedgerEntryRepository):
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def add(
        self,
        *,
        crew_order_id: uuid.UUID,
        amount: Decimal,
        entry_type: LedgerEntryTypeEnum,
        currency: CurrencyEnum,
        external_reference: str | None = None,
    ) -> CrewOrderLedgerEntry:
        model = CrewOrderLedgerEntryModel(
            crew_order_id=crew_order_id,
            amount=amount,
            entry_type=entry_type,
            currency=currency,
            external_reference=external_reference,
        )
        self._db.add(model)
        await self._db.flush()
        return _crew_order_ledger_entry_to_entity(model)

    async def sum_by_type(
        self, crew_order_id: uuid.UUID, entry_type: LedgerEntryTypeEnum
    ) -> Decimal:
        result = await self._db.execute(
            select(func.coalesce(func.sum(CrewOrderLedgerEntryModel.amount), 0)).where(
                CrewOrderLedgerEntryModel.crew_order_id == crew_order_id,
                CrewOrderLedgerEntryModel.entry_type == entry_type,
            )
        )
        return result.scalar_one()

    async def list_by_crew_order(
        self, crew_order_id: uuid.UUID, *, limit: int, offset: int
    ) -> Sequence[CrewOrderLedgerEntry]:
        result = await self._db.execute(
            select(CrewOrderLedgerEntryModel)
            .where(CrewOrderLedgerEntryModel.crew_order_id == crew_order_id)
            .order_by(CrewOrderLedgerEntryModel.created_at)
            .limit(limit)
            .offset(offset)
        )
        return [_crew_order_ledger_entry_to_entity(model) for model in result.scalars().all()]
