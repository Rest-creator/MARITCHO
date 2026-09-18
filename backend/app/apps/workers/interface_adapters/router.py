from collections.abc import Sequence

from fastapi import APIRouter, Depends, status

from app.apps.accounts.domain.entities import Person
from app.apps.accounts.interface_adapters.dependencies import RequireRole
from app.apps.workers.domain.entities import (
    ServiceArea,
    Skill,
    StandingView,
    WorkerReference,
    WorkerVettingView,
    WorkerVouch,
)
from app.apps.workers.domain.services import (
    AddReferenceUseCase,
    GetStandingUseCase,
    GetVettingViewUseCase,
    ListMyReferencesUseCase,
    ListMyServiceAreasUseCase,
    ListMySkillsUseCase,
    RegisterServiceAreaUseCase,
    RegisterSkillUseCase,
    SubmitIdPhotoUseCase,
    VouchForWorkerUseCase,
)
from app.apps.workers.interface_adapters.dependencies import (
    get_add_reference_use_case,
    get_list_my_references_use_case,
    get_list_my_service_areas_use_case,
    get_list_my_skills_use_case,
    get_register_service_area_use_case,
    get_register_skill_use_case,
    get_standing_use_case,
    get_submit_id_photo_use_case,
    get_vetting_view_use_case,
    get_vouch_for_worker_use_case,
)
from app.apps.workers.interface_adapters.schemas import (
    IdPhotoSubmit,
    ReferenceCreate,
    ReferenceOut,
    ServiceAreaCreate,
    ServiceAreaOut,
    SkillCreate,
    SkillOut,
    StandingOut,
    VouchCreate,
    VouchOut,
    WorkerVettingOut,
)
from app.core.pagination import Pagination, pagination_params
from app.shared_kernel.enums import RoleEnum

router = APIRouter(prefix="/workers/me", tags=["workers"])


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


@router.post(
    "/service-areas", response_model=ServiceAreaOut, status_code=status.HTTP_201_CREATED
)
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
) -> StandingView:
    return await use_case.execute(current_user.id)


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
