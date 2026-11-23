import uuid
from collections.abc import Sequence

from fastapi import APIRouter, Depends, Query, status
from opentelemetry import trace
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.apps.accounts.domain.entities import Person
from app.apps.accounts.interface_adapters.dependencies import RequireRole
from app.apps.jobs.infrastructure.review_models import ReviewModel
from app.apps.workers.domain.entities import (
    ServiceArea,
    Skill,
    StandingView,
    WorkerDirectoryItem,
    WorkerPublicProfile,
    WorkerReference,
    WorkerVettingView,
    WorkerVouch,
)
from app.apps.workers.domain.services import (
    AddReferenceUseCase,
    GetStandingUseCase,
    GetVettingViewUseCase,
    GetWorkerPublicProfileUseCase,
    ListMyReferencesUseCase,
    ListMyServiceAreasUseCase,
    ListMySkillsUseCase,
    ListNearbyWorkersUseCase,
    RegisterServiceAreaUseCase,
    RegisterSkillUseCase,
    SubmitIdPhotoUseCase,
    SubmitPoliceClearanceUseCase,
    VouchForWorkerUseCase,
)
from app.apps.workers.interface_adapters.dependencies import (
    get_add_reference_use_case,
    get_list_my_references_use_case,
    get_list_my_service_areas_use_case,
    get_list_my_skills_use_case,
    get_list_nearby_workers_use_case,
    get_register_service_area_use_case,
    get_register_skill_use_case,
    get_standing_use_case,
    get_submit_id_photo_use_case,
    get_submit_police_clearance_use_case,
    get_vetting_view_use_case,
    get_vouch_for_worker_use_case,
    get_worker_public_profile_use_case,
)
from app.apps.workers.interface_adapters.schemas import (
    IdPhotoSubmit,
    PoliceClearanceSubmit,
    ReferenceCreate,
    ReferenceOut,
    ServiceAreaCreate,
    ServiceAreaOut,
    SkillCreate,
    SkillOut,
    StandingOut,
    VouchCreate,
    VouchOut,
    WorkerProfileOut,
    WorkerSummaryOut,
    WorkerVettingOut,
)
from app.core.database import get_db_session
from app.core.pagination import Pagination, pagination_params
from app.core.telemetry import logger
from app.shared_kernel.enums import RoleEnum, TradeEnum

router = APIRouter(prefix="/workers/me", tags=["workers"])
directory_router = APIRouter(prefix="/workers", tags=["workers"])
tracer = trace.get_tracer(__name__)


@router.post("/skills", response_model=SkillOut, status_code=status.HTTP_201_CREATED)
async def register_skill(
    payload: SkillCreate,
    current_user: Person = Depends(RequireRole([RoleEnum.WORKER])),
    use_case: RegisterSkillUseCase = Depends(get_register_skill_use_case),
) -> Skill:
    return await use_case.execute(current_user.id, payload.trade, payload.proof_url)


@router.get("/skills", response_model=list[SkillOut])
async def list_my_skills(
    current_user: Person = Depends(RequireRole([RoleEnum.WORKER])),
    pagination: Pagination = Depends(pagination_params),
    use_case: ListMySkillsUseCase = Depends(get_list_my_skills_use_case),
) -> Sequence[Skill]:
    return await use_case.execute(current_user.id, limit=pagination.limit, offset=pagination.offset)


@router.post("/service-areas", response_model=ServiceAreaOut, status_code=status.HTTP_201_CREATED)
async def register_service_area(
    payload: ServiceAreaCreate,
    current_user: Person = Depends(RequireRole([RoleEnum.WORKER])),
    use_case: RegisterServiceAreaUseCase = Depends(get_register_service_area_use_case),
) -> ServiceArea:
    return await use_case.execute(current_user.id, payload.suburb, payload.travel_means)


@router.get("/service-areas", response_model=list[ServiceAreaOut])
async def list_my_service_areas(
    current_user: Person = Depends(RequireRole([RoleEnum.WORKER])),
    pagination: Pagination = Depends(pagination_params),
    use_case: ListMyServiceAreasUseCase = Depends(get_list_my_service_areas_use_case),
) -> Sequence[ServiceArea]:
    return await use_case.execute(current_user.id, limit=pagination.limit, offset=pagination.offset)


@router.get("/standing", response_model=StandingOut)
async def get_my_standing(
    current_user: Person = Depends(RequireRole([RoleEnum.WORKER])),
    use_case: GetStandingUseCase = Depends(get_standing_use_case),
    db: AsyncSession = Depends(get_db_session),
) -> StandingView:
    view = await use_case.execute(current_user.id)
    average, count = (
        await db.execute(
            select(func.avg(ReviewModel.rating), func.count()).where(
                ReviewModel.worker_id == current_user.id
            )
        )
    ).one()
    view.rating_average = average
    view.rating_count = count
    return view


@router.get("/vetting", response_model=WorkerVettingOut)
async def get_my_vetting(
    current_user: Person = Depends(RequireRole([RoleEnum.WORKER])),
    use_case: GetVettingViewUseCase = Depends(get_vetting_view_use_case),
) -> WorkerVettingView:
    return await use_case.execute(current_user.id)


@router.post("/vetting/id-photo", response_model=WorkerVettingOut)
async def submit_id_photo(
    payload: IdPhotoSubmit,
    current_user: Person = Depends(RequireRole([RoleEnum.WORKER])),
    use_case: SubmitIdPhotoUseCase = Depends(get_submit_id_photo_use_case),
) -> WorkerVettingView:
    """Submit (or replace) the worker's ID-photo evidence.

    Gates REGISTERED -> IDENTIFIED (ADR-005). Grade is recomputed
    immediately, same transaction, from all accumulated evidence.
    """
    return await use_case.execute(current_user.id, payload.id_photo_url)


@router.post("/vetting/police-clearance", response_model=WorkerVettingOut)
async def submit_police_clearance(
    payload: PoliceClearanceSubmit,
    current_user: Person = Depends(RequireRole([RoleEnum.WORKER])),
    use_case: SubmitPoliceClearanceUseCase = Depends(get_submit_police_clearance_use_case),
) -> WorkerVettingView:
    """Submit (or replace) the worker's Police Clearance certificate image."""
    with tracer.start_as_current_span("workers.submit_police_clearance") as span:
        span.set_attribute("worker.id", str(current_user.id))
        view = await use_case.execute(current_user.id, payload.police_clearance_url)
        span.set_attribute("worker.grade", view.grade.value)
        logger.info(
            f"Police clearance submitted by worker={current_user.id} grade={view.grade.value}"
        )
        return view


@router.post("/references", response_model=ReferenceOut, status_code=status.HTTP_201_CREATED)
async def add_reference(
    payload: ReferenceCreate,
    current_user: Person = Depends(RequireRole([RoleEnum.WORKER])),
    use_case: AddReferenceUseCase = Depends(get_add_reference_use_case),
) -> WorkerReference:
    """Add a contactable reference. Gates IDENTIFIED -> APPRENTICE (ADR-005)."""
    return await use_case.execute(current_user.id, payload.name, payload.phone)


@router.get("/references", response_model=list[ReferenceOut])
async def list_my_references(
    current_user: Person = Depends(RequireRole([RoleEnum.WORKER])),
    pagination: Pagination = Depends(pagination_params),
    use_case: ListMyReferencesUseCase = Depends(get_list_my_references_use_case),
) -> Sequence[WorkerReference]:
    return await use_case.execute(current_user.id, limit=pagination.limit, offset=pagination.offset)


@router.post("/vouches", response_model=VouchOut, status_code=status.HTTP_201_CREATED)
async def vouch_for_worker(
    payload: VouchCreate,
    current_user: Person = Depends(RequireRole([RoleEnum.WORKER])),
    use_case: VouchForWorkerUseCase = Depends(get_vouch_for_worker_use_case),
) -> WorkerVouch:
    """A JOURNEYMAN+ worker vouches for another. Gates APPRENTICE -> JOURNEYMAN/EXPERT (ADR-005).

    Recomputes the *vouched-for* worker's grade, not the voucher's.
    """
    return await use_case.execute(voucher_id=current_user.id, target_worker_id=payload.worker_id)


@directory_router.get("", response_model=list[WorkerSummaryOut])
async def list_nearby_workers(
    suburb: str | None = Query(default=None, max_length=100),
    trade: TradeEnum | None = Query(default=None),
    q: str | None = Query(default=None, max_length=200),
    current_user: Person = Depends(RequireRole([RoleEnum.BUYER])),
    pagination: Pagination = Depends(pagination_params),
    use_case: ListNearbyWorkersUseCase = Depends(get_list_nearby_workers_use_case),
) -> list[WorkerDirectoryItem]:
    """List workers ranked by proximity to `suburb` (or the caller's home_suburb)."""
    origin_suburb = suburb or current_user.home_suburb
    with tracer.start_as_current_span("workers.list_directory") as span:
        if origin_suburb:
            span.set_attribute("workers.origin_suburb", origin_suburb)
        if trade is not None:
            span.set_attribute("workers.trade", trade.value)
        results = await use_case.execute(
            suburb=origin_suburb,
            trade=trade,
            query=q,
            limit=pagination.limit,
            offset=pagination.offset,
        )
        span.set_attribute("workers.result_count", len(results))
        logger.info(
            f"Worker directory queried by user={current_user.id} "
            f"suburb={origin_suburb} hits={len(results)}"
        )
        return results


@directory_router.get("/{worker_id}", response_model=WorkerProfileOut)
async def get_worker_public_profile(
    worker_id: uuid.UUID,
    suburb: str | None = Query(default=None, max_length=100),
    current_user: Person = Depends(RequireRole([RoleEnum.BUYER])),
    use_case: GetWorkerPublicProfileUseCase = Depends(get_worker_public_profile_use_case),
) -> WorkerPublicProfile:
    """Fetch a worker's public profile, skills, standing, and past job records."""
    origin_suburb = suburb or current_user.home_suburb
    with tracer.start_as_current_span("workers.get_public_profile") as span:
        span.set_attribute("workers.target_id", str(worker_id))
        profile = await use_case.execute(worker_id, suburb=origin_suburb)
        logger.info(
            f"Worker public profile fetched by user={current_user.id} target={worker_id}"
        )
        return profile

