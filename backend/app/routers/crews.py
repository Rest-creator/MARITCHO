import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import RequireRole
from app.database import get_db_session
from app.models import Crew, CrewMember, Person, RoleEnum
from app.schemas import CrewCreate, CrewMemberAdd, CrewOut

router = APIRouter(prefix="/crews/me", tags=["crews"])


async def _crew_out(db: AsyncSession, crew: Crew) -> CrewOut:
    result = await db.execute(select(CrewMember.worker_id).where(CrewMember.crew_id == crew.id))
    member_ids = [row[0] for row in result.all()]
    return CrewOut(id=crew.id, lead_id=crew.lead_id, name=crew.name, member_ids=member_ids)


async def _get_own_crew(db: AsyncSession, current_user: Person) -> Crew:
    result = await db.execute(select(Crew).where(Crew.lead_id == current_user.id))
    crew = result.scalars().first()
    if crew is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No crew registered")
    return crew


@router.post("", response_model=CrewOut, status_code=status.HTTP_201_CREATED)
async def create_crew(
    payload: CrewCreate,
    current_user: Person = Depends(RequireRole([RoleEnum.AGGREGATOR])),
    db: AsyncSession = Depends(get_db_session),
) -> CrewOut:
    crew = Crew(lead_id=current_user.id, name=payload.name)
    db.add(crew)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You already have a crew registered",
        ) from exc
    await db.refresh(crew)
    return await _crew_out(db, crew)


@router.get("", response_model=CrewOut)
async def get_own_crew(
    current_user: Person = Depends(RequireRole([RoleEnum.AGGREGATOR])),
    db: AsyncSession = Depends(get_db_session),
) -> CrewOut:
    crew = await _get_own_crew(db, current_user)
    return await _crew_out(db, crew)


@router.post("/members", response_model=CrewOut, status_code=status.HTTP_201_CREATED)
async def add_crew_member(
    payload: CrewMemberAdd,
    current_user: Person = Depends(RequireRole([RoleEnum.AGGREGATOR])),
    db: AsyncSession = Depends(get_db_session),
) -> CrewOut:
    """The crew lead directly manages their roster (add/remove) — there is no
    invite/accept sub-workflow, matching CrewMember's plain join-table shape."""
    crew = await _get_own_crew(db, current_user)

    worker = await db.get(Person, payload.worker_id)
    if worker is None or worker.role != RoleEnum.WORKER:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="worker_id does not refer to a registered worker",
        )

    db.add(CrewMember(crew_id=crew.id, worker_id=payload.worker_id))
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Worker is already a member of this crew",
        ) from exc
    return await _crew_out(db, crew)


@router.delete("/members/{worker_id}", response_model=CrewOut)
async def remove_crew_member(
    worker_id: uuid.UUID,
    current_user: Person = Depends(RequireRole([RoleEnum.AGGREGATOR])),
    db: AsyncSession = Depends(get_db_session),
) -> CrewOut:
    crew = await _get_own_crew(db, current_user)

    member = await db.get(CrewMember, {"crew_id": crew.id, "worker_id": worker_id})
    if member is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not a crew member")

    await db.delete(member)
    await db.commit()
    return await _crew_out(db, crew)
