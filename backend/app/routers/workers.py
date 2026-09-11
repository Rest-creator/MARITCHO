import uuid
from collections.abc import Sequence
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import RequireRole
from app.database import get_db_session
from app.matching import is_worker_disputed
from app.models import GradeEnum, Person, RoleEnum, ServiceArea, Skill, Standing, Suburb
from app.pagination import Pagination, pagination_params
from app.schemas import (
    ServiceAreaCreate,
    ServiceAreaOut,
    SkillCreate,
    SkillOut,
    StandingOut,
)

router = APIRouter(prefix="/workers/me", tags=["workers"])


async def _ensure_standing(db: AsyncSession, worker_id: uuid.UUID) -> None:
    standing = await db.get(Standing, worker_id)
    if standing is None:
        db.add(Standing(worker_id=worker_id))


@router.post("/skills", response_model=SkillOut, status_code=status.HTTP_201_CREATED)
async def register_skill(
    payload: SkillCreate,
    current_user: Person = Depends(RequireRole([RoleEnum.WORKER])),
    db: AsyncSession = Depends(get_db_session),
) -> Skill:
    skill = Skill(worker_id=current_user.id, trade=payload.trade, proof_url=payload.proof_url)
    db.add(skill)
    try:
        await _ensure_standing(db, current_user.id)
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Skill already registered for this trade",
        ) from exc
    await db.refresh(skill)
    return skill


@router.get("/skills", response_model=list[SkillOut])
async def list_my_skills(
    current_user: Person = Depends(RequireRole([RoleEnum.WORKER])),
    pagination: Pagination = Depends(pagination_params),
    db: AsyncSession = Depends(get_db_session),
) -> Sequence[Skill]:
    result = await db.execute(
        select(Skill)
        .where(Skill.worker_id == current_user.id)
        .order_by(Skill.id)
        .limit(pagination.limit)
        .offset(pagination.offset)
    )
    return result.scalars().all()


@router.post(
    "/service-areas", response_model=ServiceAreaOut, status_code=status.HTTP_201_CREATED
)
async def register_service_area(
    payload: ServiceAreaCreate,
    current_user: Person = Depends(RequireRole([RoleEnum.WORKER])),
    db: AsyncSession = Depends(get_db_session),
) -> ServiceArea:
    suburb = await db.get(Suburb, payload.suburb)
    if suburb is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Unknown suburb",
        )

    area = ServiceArea(
        worker_id=current_user.id, suburb=payload.suburb, travel_means=payload.travel_means
    )
    db.add(area)
    try:
        await _ensure_standing(db, current_user.id)
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Service area already registered for this suburb",
        ) from exc
    await db.refresh(area)
    return area


@router.get("/service-areas", response_model=list[ServiceAreaOut])
async def list_my_service_areas(
    current_user: Person = Depends(RequireRole([RoleEnum.WORKER])),
    pagination: Pagination = Depends(pagination_params),
    db: AsyncSession = Depends(get_db_session),
) -> Sequence[ServiceArea]:
    result = await db.execute(
        select(ServiceArea)
        .where(ServiceArea.worker_id == current_user.id)
        .order_by(ServiceArea.id)
        .limit(pagination.limit)
        .offset(pagination.offset)
    )
    return result.scalars().all()


@router.get("/standing", response_model=StandingOut)
async def get_my_standing(
    current_user: Person = Depends(RequireRole([RoleEnum.WORKER])),
    db: AsyncSession = Depends(get_db_session),
) -> StandingOut:
    standing = await db.get(Standing, current_user.id)
    frozen = await is_worker_disputed(db, current_user.id)

    if standing is not None:
        return StandingOut(
            worker_id=standing.worker_id,
            grade=standing.grade or GradeEnum.REGISTERED,
            on_time_rate=(
                standing.on_time_rate if standing.on_time_rate is not None else Decimal("100.00")
            ),
            dispute_rate=(
                standing.dispute_rate if standing.dispute_rate is not None else Decimal("0.00")
            ),
            fill_rate=standing.fill_rate if standing.fill_rate is not None else Decimal("0.00"),
            jobs_completed=(
                standing.jobs_completed if standing.jobs_completed is not None else 0
            ),
            is_frozen=frozen,
        )

    # A worker with nothing registered yet still has a "computed" standing:
    # the same defaults the standings table would give them on first insert.
    return StandingOut(
        worker_id=current_user.id,
        grade=GradeEnum.REGISTERED,
        on_time_rate=Decimal("100.00"),
        dispute_rate=Decimal("0.00"),
        fill_rate=Decimal("0.00"),
        jobs_completed=0,
        is_frozen=frozen,
    )
