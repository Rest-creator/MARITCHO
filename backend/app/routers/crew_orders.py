import uuid
from collections.abc import Sequence

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import RequireRole, get_current_user
from app.crew_matching import find_top_crew_candidates, is_crew_busy
from app.database import get_db_session
from app.ledger import sum_crew_order_ledger_entries
from app.models import (
    Crew,
    CrewOrder,
    CrewOrderLedgerEntry,
    CrewOrderStatusEnum,
    LedgerEntryTypeEnum,
    Person,
    RoleEnum,
    Suburb,
)
from app.pagination import Pagination, pagination_params
from app.schemas import (
    CrewBookingCreate,
    CrewMatchCandidateOut,
    CrewOrderCompletionCreate,
    CrewOrderCreate,
    CrewOrderLedgerEntryOut,
    CrewOrderOut,
    CrewOrderQuoteCreate,
)

router = APIRouter(prefix="/crew-orders", tags=["crew-orders"])


async def _get_crew_lead_id(db: AsyncSession, order: CrewOrder) -> uuid.UUID | None:
    if order.crew_id is None:
        return None
    crew = await db.get(Crew, order.crew_id)
    return crew.lead_id if crew else None


async def _require_party(db: AsyncSession, order: CrewOrder, current_user: Person) -> None:
    lead_id = await _get_crew_lead_id(db, order)
    is_party = current_user.id == order.buyer_id or (
        lead_id is not None and current_user.id == lead_id
    )
    if not is_party and current_user.role != RoleEnum.OPS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not permitted to view this crew order",
        )


@router.post("/request", response_model=CrewOrderOut, status_code=status.HTTP_201_CREATED)
async def create_crew_order(
    payload: CrewOrderCreate,
    current_user: Person = Depends(RequireRole([RoleEnum.BUYER])),
    db: AsyncSession = Depends(get_db_session),
) -> CrewOrder:
    """An organization requests a crew (N workers of a trade) for a site."""
    suburb = await db.get(Suburb, payload.suburb)
    if suburb is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Unknown suburb",
        )

    order = CrewOrder(
        buyer_id=current_user.id,
        status=CrewOrderStatusEnum.REQUESTED,
        trade=payload.trade,
        suburb=payload.suburb,
        address=payload.address,
        workers_needed=payload.workers_needed,
        problem_description=payload.problem_description,
    )
    db.add(order)
    await db.commit()
    await db.refresh(order)
    return order


@router.get("/{order_id}", response_model=CrewOrderOut)
async def get_crew_order(
    order_id: uuid.UUID,
    current_user: Person = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> CrewOrder:
    order = await db.get(CrewOrder, order_id)
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Crew order not found")

    await _require_party(db, order, current_user)
    return order


@router.get("/{order_id}/matches", response_model=list[CrewMatchCandidateOut])
async def get_crew_order_matches(
    order_id: uuid.UUID,
    current_user: Person = Depends(RequireRole([RoleEnum.BUYER])),
    db: AsyncSession = Depends(get_db_session),
) -> list[CrewMatchCandidateOut]:
    """Run the crew matching engine and return up to 3 ranked crew candidates."""
    order = await db.get(CrewOrder, order_id)
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Crew order not found")

    if order.buyer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not permitted to view matches for this crew order",
        )

    if order.status not in (CrewOrderStatusEnum.REQUESTED, CrewOrderStatusEnum.MATCHED):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Crew order is no longer accepting matches",
        )

    candidates = await find_top_crew_candidates(db, order)

    if order.status == CrewOrderStatusEnum.REQUESTED:
        order.status = CrewOrderStatusEnum.MATCHED
        await db.commit()

    return candidates


@router.post("/{order_id}/book", response_model=CrewOrderOut)
async def book_crew_order(
    order_id: uuid.UUID,
    payload: CrewBookingCreate,
    current_user: Person = Depends(RequireRole([RoleEnum.BUYER])),
    db: AsyncSession = Depends(get_db_session),
) -> CrewOrder:
    """Book a matched crew: holds the deposit. The crew becomes unavailable
    (as a whole) for other orders until this one completes."""
    order = await db.get(CrewOrder, order_id)
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Crew order not found")

    if order.buyer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not permitted to book this crew order",
        )

    if order.status != CrewOrderStatusEnum.MATCHED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Crew order must be MATCHED before it can be booked",
        )

    crew = await db.get(Crew, payload.crew_id)
    if crew is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="crew_id does not refer to a registered crew",
        )

    if await is_crew_busy(db, crew.id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Crew is already committed to another active order",
        )

    order.crew_id = crew.id
    order.status = CrewOrderStatusEnum.BOOKED
    db.add(
        CrewOrderLedgerEntry(
            crew_order_id=order.id,
            amount=payload.deposit_amount,
            entry_type=LedgerEntryTypeEnum.DEPOSIT_HELD,
        )
    )
    await db.commit()
    await db.refresh(order)
    return order


@router.post("/{order_id}/quote", response_model=CrewOrderOut)
async def submit_crew_order_quote(
    order_id: uuid.UUID,
    payload: CrewOrderQuoteCreate,
    current_user: Person = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> CrewOrder:
    """The booked crew's lead submits their on-site price assessment."""
    order = await db.get(CrewOrder, order_id)
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Crew order not found")

    lead_id = await _get_crew_lead_id(db, order)
    if lead_id is None or current_user.id != lead_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not permitted to submit a quote for this crew order",
        )

    if order.status != CrewOrderStatusEnum.BOOKED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Crew order must be BOOKED before a quote can be submitted",
        )

    deposit_total = await sum_crew_order_ledger_entries(
        db, order.id, LedgerEntryTypeEnum.DEPOSIT_HELD
    )
    if payload.quote_amount <= deposit_total:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Quote must exceed the deposit already held",
        )

    order.quote_amount = payload.quote_amount
    order.status = CrewOrderStatusEnum.IN_PROGRESS
    db.add(
        CrewOrderLedgerEntry(
            crew_order_id=order.id,
            amount=payload.quote_amount - deposit_total,
            entry_type=LedgerEntryTypeEnum.BALANCE_COMMITTED,
        )
    )
    await db.commit()
    await db.refresh(order)
    return order


@router.post("/{order_id}/complete", response_model=CrewOrderOut)
async def complete_crew_order(
    order_id: uuid.UUID,
    payload: CrewOrderCompletionCreate,
    current_user: Person = Depends(RequireRole([RoleEnum.BUYER])),
    db: AsyncSession = Depends(get_db_session),
) -> CrewOrder:
    """Buyer signs off and releases the balance. No per-worker RecordEntry is
    written for crew orders — see database_schema_design.md for why."""
    order = await db.get(CrewOrder, order_id)
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Crew order not found")

    if order.buyer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not permitted to complete this crew order",
        )

    if order.status != CrewOrderStatusEnum.IN_PROGRESS:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Crew order must be IN_PROGRESS before it can be completed",
        )

    order.completion_note = payload.what_was_done
    order.status = CrewOrderStatusEnum.COMPLETED
    db.add(
        CrewOrderLedgerEntry(
            crew_order_id=order.id,
            amount=order.quote_amount,
            entry_type=LedgerEntryTypeEnum.RELEASED,
        )
    )
    await db.commit()
    await db.refresh(order)
    return order


@router.get("/{order_id}/ledger", response_model=list[CrewOrderLedgerEntryOut])
async def get_crew_order_ledger(
    order_id: uuid.UUID,
    current_user: Person = Depends(get_current_user),
    pagination: Pagination = Depends(pagination_params),
    db: AsyncSession = Depends(get_db_session),
) -> Sequence[CrewOrderLedgerEntry]:
    order = await db.get(CrewOrder, order_id)
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Crew order not found")

    await _require_party(db, order, current_user)

    result = await db.execute(
        select(CrewOrderLedgerEntry)
        .where(CrewOrderLedgerEntry.crew_order_id == order_id)
        .order_by(CrewOrderLedgerEntry.created_at)
        .limit(pagination.limit)
        .offset(pagination.offset)
    )
    return result.scalars().all()
