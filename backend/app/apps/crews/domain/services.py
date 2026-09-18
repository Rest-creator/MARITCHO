import uuid
from collections.abc import Sequence
from decimal import Decimal

from app.apps.accounts.domain.repositories import PersonRepository
from app.apps.crews.domain.entities import (
    CrewMatchCandidate,
    CrewOrder,
    CrewOrderLedgerEntry,
    CrewOrderStatusEnum,
    CrewView,
)
from app.apps.crews.domain.matching import CrewMatchingService
from app.apps.crews.domain.repositories import (
    CrewMemberRepository,
    CrewOrderLedgerEntryRepository,
    CrewOrderRepository,
    CrewRepository,
)
from app.core.exceptions import (
    ConflictError,
    ForbiddenError,
    IntegrityConflictError,
    NotFoundError,
    ValidationConflictError,
)
from app.shared_kernel.enums import CurrencyEnum, LedgerEntryTypeEnum, RoleEnum, TradeEnum
from app.shared_kernel.ports import PaymentCollectionPort, SuburbLookupPort
from app.shared_kernel.unit_of_work import UnitOfWork


async def _get_crew_lead_id(crews: CrewRepository, order: CrewOrder) -> uuid.UUID | None:
    if order.crew_id is None:
        return None
    crew = await crews.get(order.crew_id)
    return crew.lead_id if crew else None


def _require_crew_order_party(
    order: CrewOrder,
    lead_id: uuid.UUID | None,
    current_user_id: uuid.UUID,
    current_user_role: RoleEnum,
) -> None:
    is_party = current_user_id == order.buyer_id or (
        lead_id is not None and current_user_id == lead_id
    )
    if not is_party and current_user_role != RoleEnum.OPS:
        raise ForbiddenError("Not permitted to view this crew order")


class CreateCrewUseCase:
    def __init__(self, crews: CrewRepository, uow: UnitOfWork) -> None:
        self._crews = crews
        self._uow = uow

    async def execute(self, lead_id: uuid.UUID, name: str) -> CrewView:
        try:
            crew = await self._crews.create(lead_id=lead_id, name=name)
        except IntegrityConflictError as exc:
            raise ConflictError("You already have a crew registered") from exc
        await self._uow.commit()
        return CrewView(id=crew.id, lead_id=crew.lead_id, name=crew.name, member_ids=[])


class GetOwnCrewUseCase:
    def __init__(self, crews: CrewRepository, members: CrewMemberRepository) -> None:
        self._crews = crews
        self._members = members

    async def execute(self, lead_id: uuid.UUID) -> CrewView:
        crew = await self._crews.get_by_lead(lead_id)
        if crew is None:
            raise NotFoundError("No crew registered")
        member_ids = await self._members.list_worker_ids_by_crew(crew.id)
        return CrewView(id=crew.id, lead_id=crew.lead_id, name=crew.name, member_ids=member_ids)


class AddCrewMemberUseCase:
    """The crew lead directly manages their roster (add/remove) — there is
    no invite/accept sub-workflow, matching CrewMember's plain join-table shape."""

    def __init__(
        self,
        crews: CrewRepository,
        members: CrewMemberRepository,
        persons: PersonRepository,
        uow: UnitOfWork,
    ) -> None:
        self._crews = crews
        self._members = members
        self._persons = persons
        self._uow = uow

    async def execute(self, lead_id: uuid.UUID, worker_id: uuid.UUID) -> CrewView:
        crew = await self._crews.get_by_lead(lead_id)
        if crew is None:
            raise NotFoundError("No crew registered")

        worker = await self._persons.get_by_id(worker_id)
        if worker is None or worker.role != RoleEnum.WORKER:
            raise ValidationConflictError("worker_id does not refer to a registered worker")

        try:
            await self._members.add(crew_id=crew.id, worker_id=worker_id)
        except IntegrityConflictError as exc:
            raise ConflictError("Worker is already a member of this crew") from exc

        await self._uow.commit()
        member_ids = await self._members.list_worker_ids_by_crew(crew.id)
        return CrewView(id=crew.id, lead_id=crew.lead_id, name=crew.name, member_ids=member_ids)


class RemoveCrewMemberUseCase:
    def __init__(
        self, crews: CrewRepository, members: CrewMemberRepository, uow: UnitOfWork
    ) -> None:
        self._crews = crews
        self._members = members
        self._uow = uow

    async def execute(self, lead_id: uuid.UUID, worker_id: uuid.UUID) -> CrewView:
        crew = await self._crews.get_by_lead(lead_id)
        if crew is None:
            raise NotFoundError("No crew registered")

        member = await self._members.get(crew.id, worker_id)
        if member is None:
            raise NotFoundError("Not a crew member")

        await self._members.remove(member)
        await self._uow.commit()
        member_ids = await self._members.list_worker_ids_by_crew(crew.id)
        return CrewView(id=crew.id, lead_id=crew.lead_id, name=crew.name, member_ids=member_ids)


class CreateCrewOrderUseCase:
    """An organization requests a crew (N workers of a trade) for a site."""

    def __init__(
        self, orders: CrewOrderRepository, suburbs: SuburbLookupPort, uow: UnitOfWork
    ) -> None:
        self._orders = orders
        self._suburbs = suburbs
        self._uow = uow

    async def execute(
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
        if not await self._suburbs.exists(suburb):
            raise ValidationConflictError("Unknown suburb")

        order = await self._orders.create(
            buyer_id=buyer_id,
            trade=trade,
            suburb=suburb,
            address=address,
            landmark_narrative=landmark_narrative,
            latitude=latitude,
            longitude=longitude,
            workers_needed=workers_needed,
            problem_description=problem_description,
        )
        await self._uow.commit()
        return order


class GetCrewOrderUseCase:
    def __init__(self, orders: CrewOrderRepository, crews: CrewRepository) -> None:
        self._orders = orders
        self._crews = crews

    async def execute(
        self, order_id: uuid.UUID, current_user_id: uuid.UUID, current_user_role: RoleEnum
    ) -> CrewOrder:
        order = await self._orders.get(order_id)
        if order is None:
            raise NotFoundError("Crew order not found")
        lead_id = await _get_crew_lead_id(self._crews, order)
        _require_crew_order_party(order, lead_id, current_user_id, current_user_role)
        return order


class GetCrewOrderMatchesUseCase:
    """Run the crew matching engine and return up to 3 ranked crew candidates."""

    def __init__(
        self, orders: CrewOrderRepository, matching: CrewMatchingService, uow: UnitOfWork
    ) -> None:
        self._orders = orders
        self._matching = matching
        self._uow = uow

    async def execute(
        self, order_id: uuid.UUID, current_user_id: uuid.UUID
    ) -> list[CrewMatchCandidate]:
        order = await self._orders.get(order_id)
        if order is None:
            raise NotFoundError("Crew order not found")

        if order.buyer_id != current_user_id:
            raise ForbiddenError("Not permitted to view matches for this crew order")

        if order.status not in (CrewOrderStatusEnum.REQUESTED, CrewOrderStatusEnum.MATCHED):
            raise ConflictError("Crew order is no longer accepting matches")

        candidates = await self._matching.find_top_candidates(order)

        if order.status == CrewOrderStatusEnum.REQUESTED:
            order.status = CrewOrderStatusEnum.MATCHED
            await self._orders.save(order)
            await self._uow.commit()

        return candidates


class BookCrewOrderUseCase:
    """Book a matched crew: holds the deposit. The crew becomes unavailable
    (as a whole) for other orders until this one completes."""

    def __init__(
        self,
        orders: CrewOrderRepository,
        crews: CrewRepository,
        ledger: CrewOrderLedgerEntryRepository,
        payment_gateway: PaymentCollectionPort,
        uow: UnitOfWork,
    ) -> None:
        self._orders = orders
        self._crews = crews
        self._ledger = ledger
        self._payment_gateway = payment_gateway
        self._uow = uow

    async def execute(
        self,
        *,
        order_id: uuid.UUID,
        buyer_id: uuid.UUID,
        buyer_phone: str,
        crew_id: uuid.UUID,
        deposit_amount: Decimal,
        currency: CurrencyEnum,
    ) -> CrewOrder:
        order = await self._orders.get(order_id)
        if order is None:
            raise NotFoundError("Crew order not found")

        if order.buyer_id != buyer_id:
            raise ForbiddenError("Not permitted to book this crew order")

        if order.status != CrewOrderStatusEnum.MATCHED:
            raise ConflictError("Crew order must be MATCHED before it can be booked")

        crew = await self._crews.get(crew_id)
        if crew is None:
            raise ValidationConflictError("crew_id does not refer to a registered crew")

        if await self._orders.is_crew_busy(crew.id):
            raise ConflictError("Crew is already committed to another active order")

        external_reference = None
        if currency == CurrencyEnum.ECOCASH:
            external_reference = await self._payment_gateway.initiate_collection(
                phone=buyer_phone,
                amount=deposit_amount,
                reference=str(order.id),
            )

        order.crew_id = crew.id
        order.status = CrewOrderStatusEnum.BOOKED
        order.currency = currency
        await self._orders.save(order)
        await self._ledger.add(
            crew_order_id=order.id,
            amount=deposit_amount,
            entry_type=LedgerEntryTypeEnum.DEPOSIT_HELD,
            currency=currency,
            external_reference=external_reference,
        )
        await self._uow.commit()
        return order


class SubmitCrewOrderQuoteUseCase:
    """The booked crew's lead submits their on-site price assessment."""

    def __init__(
        self,
        orders: CrewOrderRepository,
        crews: CrewRepository,
        ledger: CrewOrderLedgerEntryRepository,
        uow: UnitOfWork,
    ) -> None:
        self._orders = orders
        self._crews = crews
        self._ledger = ledger
        self._uow = uow

    async def execute(
        self,
        *,
        order_id: uuid.UUID,
        current_user_id: uuid.UUID,
        labor_amount: Decimal,
        materials_amount: Decimal,
    ) -> CrewOrder:
        order = await self._orders.get(order_id)
        if order is None:
            raise NotFoundError("Crew order not found")

        lead_id = await _get_crew_lead_id(self._crews, order)
        if lead_id is None or current_user_id != lead_id:
            raise ForbiddenError("Not permitted to submit a quote for this crew order")

        if order.status != CrewOrderStatusEnum.BOOKED:
            raise ConflictError("Crew order must be BOOKED before a quote can be submitted")

        quote_amount = labor_amount + materials_amount
        deposit_total = await self._ledger.sum_by_type(order.id, LedgerEntryTypeEnum.DEPOSIT_HELD)
        if quote_amount <= deposit_total:
            raise ValidationConflictError("Quote must exceed the deposit already held")

        assert order.currency is not None, "BOOKED implies a currency was set"
        order.labor_amount = labor_amount
        order.materials_amount = materials_amount
        order.quote_amount = quote_amount
        order.status = CrewOrderStatusEnum.IN_PROGRESS
        await self._orders.save(order)
        await self._ledger.add(
            crew_order_id=order.id,
            amount=quote_amount - deposit_total,
            entry_type=LedgerEntryTypeEnum.BALANCE_COMMITTED,
            currency=order.currency,
        )
        await self._uow.commit()
        return order


class CompleteCrewOrderUseCase:
    """Buyer signs off and releases the balance. No per-worker RecordEntry is
    written for crew orders, and no per-worker standing recompute either —
    crew booking commits the whole crew as one unit and doesn't track which
    members actually worked (see database_schema_design.md)."""

    def __init__(
        self, orders: CrewOrderRepository, ledger: CrewOrderLedgerEntryRepository, uow: UnitOfWork
    ) -> None:
        self._orders = orders
        self._ledger = ledger
        self._uow = uow

    async def execute(
        self, *, order_id: uuid.UUID, buyer_id: uuid.UUID, what_was_done: str
    ) -> CrewOrder:
        order = await self._orders.get(order_id)
        if order is None:
            raise NotFoundError("Crew order not found")

        if order.buyer_id != buyer_id:
            raise ForbiddenError("Not permitted to complete this crew order")

        if order.status != CrewOrderStatusEnum.IN_PROGRESS:
            raise ConflictError("Crew order must be IN_PROGRESS before it can be completed")

        assert order.currency is not None, "IN_PROGRESS implies a currency was set"
        assert order.quote_amount is not None, "IN_PROGRESS implies a quote was submitted"
        order.completion_note = what_was_done
        order.status = CrewOrderStatusEnum.COMPLETED
        await self._orders.save(order)
        await self._ledger.add(
            crew_order_id=order.id,
            amount=order.quote_amount,
            entry_type=LedgerEntryTypeEnum.RELEASED,
            currency=order.currency,
        )
        await self._uow.commit()
        return order


class GetCrewOrderLedgerUseCase:
    def __init__(
        self,
        orders: CrewOrderRepository,
        crews: CrewRepository,
        ledger: CrewOrderLedgerEntryRepository,
    ) -> None:
        self._orders = orders
        self._crews = crews
        self._ledger = ledger

    async def execute(
        self,
        order_id: uuid.UUID,
        current_user_id: uuid.UUID,
        current_user_role: RoleEnum,
        *,
        limit: int,
        offset: int,
    ) -> Sequence[CrewOrderLedgerEntry]:
        order = await self._orders.get(order_id)
        if order is None:
            raise NotFoundError("Crew order not found")
        lead_id = await _get_crew_lead_id(self._crews, order)
        _require_crew_order_party(order, lead_id, current_user_id, current_user_role)
        return await self._ledger.list_by_crew_order(order_id, limit=limit, offset=offset)
