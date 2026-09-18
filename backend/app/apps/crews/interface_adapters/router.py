import uuid
from collections.abc import Sequence

from fastapi import APIRouter, Depends, status

from app.apps.accounts.domain.entities import Person
from app.apps.accounts.interface_adapters.dependencies import RequireRole, get_current_user
from app.apps.crews.domain.entities import (
    CrewMatchCandidate,
    CrewOrder,
    CrewOrderLedgerEntry,
    CrewView,
)
from app.apps.crews.domain.services import (
    AddCrewMemberUseCase,
    BookCrewOrderUseCase,
    CompleteCrewOrderUseCase,
    CreateCrewOrderUseCase,
    CreateCrewUseCase,
    GetCrewOrderLedgerUseCase,
    GetCrewOrderMatchesUseCase,
    GetCrewOrderUseCase,
    GetOwnCrewUseCase,
    RemoveCrewMemberUseCase,
    SubmitCrewOrderQuoteUseCase,
)
from app.apps.crews.interface_adapters.dependencies import (
    get_add_crew_member_use_case,
    get_book_crew_order_use_case,
    get_complete_crew_order_use_case,
    get_create_crew_order_use_case,
    get_create_crew_use_case,
    get_get_crew_order_ledger_use_case,
    get_get_crew_order_matches_use_case,
    get_get_crew_order_use_case,
    get_get_own_crew_use_case,
    get_remove_crew_member_use_case,
    get_submit_crew_order_quote_use_case,
)
from app.apps.crews.interface_adapters.schemas import (
    CrewBookingCreate,
    CrewCreate,
    CrewMatchCandidateOut,
    CrewMemberAdd,
    CrewOrderCompletionCreate,
    CrewOrderCreate,
    CrewOrderLedgerEntryOut,
    CrewOrderOut,
    CrewOrderQuoteCreate,
    CrewOut,
)
from app.core.pagination import Pagination, pagination_params
from app.shared_kernel.enums import RoleEnum

crews_router = APIRouter(prefix="/crews/me", tags=["crews"])
crew_orders_router = APIRouter(prefix="/crew-orders", tags=["crew-orders"])


@crews_router.post("", response_model=CrewOut, status_code=status.HTTP_201_CREATED)
async def create_crew(
    payload: CrewCreate,
    current_user: Person = Depends(RequireRole([RoleEnum.AGGREGATOR])),
    use_case: CreateCrewUseCase = Depends(get_create_crew_use_case),
) -> CrewView:
    return await use_case.execute(current_user.id, payload.name)


@crews_router.get("", response_model=CrewOut)
async def get_own_crew(
    current_user: Person = Depends(RequireRole([RoleEnum.AGGREGATOR])),
    use_case: GetOwnCrewUseCase = Depends(get_get_own_crew_use_case),
) -> CrewView:
    return await use_case.execute(current_user.id)


@crews_router.post("/members", response_model=CrewOut, status_code=status.HTTP_201_CREATED)
async def add_crew_member(
    payload: CrewMemberAdd,
    current_user: Person = Depends(RequireRole([RoleEnum.AGGREGATOR])),
    use_case: AddCrewMemberUseCase = Depends(get_add_crew_member_use_case),
) -> CrewView:
    """The crew lead directly manages their roster (add/remove) — there is no
    invite/accept sub-workflow, matching CrewMember's plain join-table shape."""
    return await use_case.execute(current_user.id, payload.worker_id)


@crews_router.delete("/members/{worker_id}", response_model=CrewOut)
async def remove_crew_member(
    worker_id: uuid.UUID,
    current_user: Person = Depends(RequireRole([RoleEnum.AGGREGATOR])),
    use_case: RemoveCrewMemberUseCase = Depends(get_remove_crew_member_use_case),
) -> CrewView:
    return await use_case.execute(current_user.id, worker_id)


@crew_orders_router.post(
    "/request", response_model=CrewOrderOut, status_code=status.HTTP_201_CREATED
)
async def create_crew_order(
    payload: CrewOrderCreate,
    current_user: Person = Depends(RequireRole([RoleEnum.BUYER])),
    use_case: CreateCrewOrderUseCase = Depends(get_create_crew_order_use_case),
) -> CrewOrder:
    """An organization requests a crew (N workers of a trade) for a site."""
    return await use_case.execute(
        buyer_id=current_user.id,
        trade=payload.trade,
        suburb=payload.suburb,
        address=payload.address,
        landmark_narrative=payload.landmark_narrative,
        latitude=payload.latitude,
        longitude=payload.longitude,
        workers_needed=payload.workers_needed,
        problem_description=payload.problem_description,
    )


@crew_orders_router.get("/{order_id}", response_model=CrewOrderOut)
async def get_crew_order(
    order_id: uuid.UUID,
    current_user: Person = Depends(get_current_user),
    use_case: GetCrewOrderUseCase = Depends(get_get_crew_order_use_case),
) -> CrewOrder:
    return await use_case.execute(order_id, current_user.id, current_user.role)


@crew_orders_router.get("/{order_id}/matches", response_model=list[CrewMatchCandidateOut])
async def get_crew_order_matches(
    order_id: uuid.UUID,
    current_user: Person = Depends(RequireRole([RoleEnum.BUYER])),
    use_case: GetCrewOrderMatchesUseCase = Depends(get_get_crew_order_matches_use_case),
) -> list[CrewMatchCandidate]:
    """Run the crew matching engine and return up to 3 ranked crew candidates."""
    return await use_case.execute(order_id, current_user.id)


@crew_orders_router.post("/{order_id}/book", response_model=CrewOrderOut)
async def book_crew_order(
    order_id: uuid.UUID,
    payload: CrewBookingCreate,
    current_user: Person = Depends(RequireRole([RoleEnum.BUYER])),
    use_case: BookCrewOrderUseCase = Depends(get_book_crew_order_use_case),
) -> CrewOrder:
    """Book a matched crew: holds the deposit. The crew becomes unavailable
    (as a whole) for other orders until this one completes."""
    return await use_case.execute(
        order_id=order_id,
        buyer_id=current_user.id,
        buyer_phone=current_user.phone,
        crew_id=payload.crew_id,
        deposit_amount=payload.deposit_amount,
        currency=payload.currency,
    )


@crew_orders_router.post("/{order_id}/quote", response_model=CrewOrderOut)
async def submit_crew_order_quote(
    order_id: uuid.UUID,
    payload: CrewOrderQuoteCreate,
    current_user: Person = Depends(get_current_user),
    use_case: SubmitCrewOrderQuoteUseCase = Depends(get_submit_crew_order_quote_use_case),
) -> CrewOrder:
    """The booked crew's lead submits their on-site price assessment."""
    return await use_case.execute(
        order_id=order_id,
        current_user_id=current_user.id,
        labor_amount=payload.labor_amount,
        materials_amount=payload.materials_amount,
    )


@crew_orders_router.post("/{order_id}/complete", response_model=CrewOrderOut)
async def complete_crew_order(
    order_id: uuid.UUID,
    payload: CrewOrderCompletionCreate,
    current_user: Person = Depends(RequireRole([RoleEnum.BUYER])),
    use_case: CompleteCrewOrderUseCase = Depends(get_complete_crew_order_use_case),
) -> CrewOrder:
    """Buyer signs off and releases the balance. No per-worker RecordEntry is
    written for crew orders — see database_schema_design.md for why."""
    return await use_case.execute(
        order_id=order_id, buyer_id=current_user.id, what_was_done=payload.what_was_done
    )


@crew_orders_router.get("/{order_id}/ledger", response_model=list[CrewOrderLedgerEntryOut])
async def get_crew_order_ledger(
    order_id: uuid.UUID,
    current_user: Person = Depends(get_current_user),
    pagination: Pagination = Depends(pagination_params),
    use_case: GetCrewOrderLedgerUseCase = Depends(get_get_crew_order_ledger_use_case),
) -> Sequence[CrewOrderLedgerEntry]:
    return await use_case.execute(
        order_id,
        current_user.id,
        current_user.role,
        limit=pagination.limit,
        offset=pagination.offset,
    )
