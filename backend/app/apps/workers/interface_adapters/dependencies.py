from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.apps.accounts.infrastructure.repositories import SqlAlchemyPersonRepository
from app.apps.accounts.interface_adapters.dependencies import get_person_repository
from app.apps.suburbs.infrastructure.repositories import SqlAlchemySuburbRepository
from app.apps.suburbs.interface_adapters.dependencies import get_suburb_repository
from app.apps.workers.domain.services import (
    AddReferenceUseCase,
    GetStandingUseCase,
    GetVettingViewUseCase,
    ListMyReferencesUseCase,
    ListMyServiceAreasUseCase,
    ListMySkillsUseCase,
    RecomputeGradeUseCase,
    RegisterServiceAreaUseCase,
    RegisterSkillUseCase,
    SubmitIdPhotoUseCase,
    VouchForWorkerUseCase,
)
from app.apps.workers.infrastructure.repositories import (
    SqlAlchemyServiceAreaRepository,
    SqlAlchemySkillRepository,
    SqlAlchemyStandingRepository,
    SqlAlchemyWorkerReferenceRepository,
    SqlAlchemyWorkerVettingRepository,
    SqlAlchemyWorkerVouchRepository,
)
from app.core.database import get_db_session
from app.core.unit_of_work import SqlAlchemyUnitOfWork, get_unit_of_work


def get_skill_repository(db: AsyncSession = Depends(get_db_session)) -> SqlAlchemySkillRepository:
    return SqlAlchemySkillRepository(db)


def get_service_area_repository(
    db: AsyncSession = Depends(get_db_session),
) -> SqlAlchemyServiceAreaRepository:
    return SqlAlchemyServiceAreaRepository(db)


def get_standing_repository(
    db: AsyncSession = Depends(get_db_session),
) -> SqlAlchemyStandingRepository:
    return SqlAlchemyStandingRepository(db)


def get_worker_vetting_repository(
    db: AsyncSession = Depends(get_db_session),
) -> SqlAlchemyWorkerVettingRepository:
    return SqlAlchemyWorkerVettingRepository(db)


def get_worker_reference_repository(
    db: AsyncSession = Depends(get_db_session),
) -> SqlAlchemyWorkerReferenceRepository:
    return SqlAlchemyWorkerReferenceRepository(db)


def get_worker_vouch_repository(
    db: AsyncSession = Depends(get_db_session),
) -> SqlAlchemyWorkerVouchRepository:
    return SqlAlchemyWorkerVouchRepository(db)


def get_register_skill_use_case(
    skills: SqlAlchemySkillRepository = Depends(get_skill_repository),
    standings: SqlAlchemyStandingRepository = Depends(get_standing_repository),
    uow: SqlAlchemyUnitOfWork = Depends(get_unit_of_work),
) -> RegisterSkillUseCase:
    return RegisterSkillUseCase(skills, standings, uow)


def get_list_my_skills_use_case(
    skills: SqlAlchemySkillRepository = Depends(get_skill_repository),
) -> ListMySkillsUseCase:
    return ListMySkillsUseCase(skills)


def get_register_service_area_use_case(
    service_areas: SqlAlchemyServiceAreaRepository = Depends(get_service_area_repository),
    standings: SqlAlchemyStandingRepository = Depends(get_standing_repository),
    suburbs: SqlAlchemySuburbRepository = Depends(get_suburb_repository),
    uow: SqlAlchemyUnitOfWork = Depends(get_unit_of_work),
) -> RegisterServiceAreaUseCase:
    return RegisterServiceAreaUseCase(service_areas, standings, suburbs, uow)


def get_list_my_service_areas_use_case(
    service_areas: SqlAlchemyServiceAreaRepository = Depends(get_service_area_repository),
) -> ListMyServiceAreasUseCase:
    return ListMyServiceAreasUseCase(service_areas)


def get_standing_use_case(
    standings: SqlAlchemyStandingRepository = Depends(get_standing_repository),
    db: AsyncSession = Depends(get_db_session),
) -> GetStandingUseCase:
    # Local import: WorkerAvailabilityPort is owned by the jobs app
    # (dispute status lives on Job/Dispute), which itself depends on this
    # (workers) app for skill/standing checks — importing at call time
    # instead of module level avoids a load-order dependency between the
    # two apps' interface_adapters packages.
    from app.apps.jobs.interface_adapters.dependencies import get_job_repository

    availability = get_job_repository(db)
    return GetStandingUseCase(standings, availability)


def get_recompute_grade_use_case(
    standings: SqlAlchemyStandingRepository = Depends(get_standing_repository),
    vetting: SqlAlchemyWorkerVettingRepository = Depends(get_worker_vetting_repository),
    references: SqlAlchemyWorkerReferenceRepository = Depends(get_worker_reference_repository),
    vouches: SqlAlchemyWorkerVouchRepository = Depends(get_worker_vouch_repository),
) -> RecomputeGradeUseCase:
    return RecomputeGradeUseCase(standings, vetting, references, vouches)


def get_vetting_view_use_case(
    vetting: SqlAlchemyWorkerVettingRepository = Depends(get_worker_vetting_repository),
    references: SqlAlchemyWorkerReferenceRepository = Depends(get_worker_reference_repository),
    vouches: SqlAlchemyWorkerVouchRepository = Depends(get_worker_vouch_repository),
    standings: SqlAlchemyStandingRepository = Depends(get_standing_repository),
) -> GetVettingViewUseCase:
    return GetVettingViewUseCase(vetting, references, vouches, standings)


def get_submit_id_photo_use_case(
    vetting: SqlAlchemyWorkerVettingRepository = Depends(get_worker_vetting_repository),
    standings: SqlAlchemyStandingRepository = Depends(get_standing_repository),
    uow: SqlAlchemyUnitOfWork = Depends(get_unit_of_work),
    recompute_grade: RecomputeGradeUseCase = Depends(get_recompute_grade_use_case),
    view: GetVettingViewUseCase = Depends(get_vetting_view_use_case),
) -> SubmitIdPhotoUseCase:
    return SubmitIdPhotoUseCase(vetting, standings, uow, recompute_grade, view)


def get_add_reference_use_case(
    references: SqlAlchemyWorkerReferenceRepository = Depends(get_worker_reference_repository),
    standings: SqlAlchemyStandingRepository = Depends(get_standing_repository),
    uow: SqlAlchemyUnitOfWork = Depends(get_unit_of_work),
    recompute_grade: RecomputeGradeUseCase = Depends(get_recompute_grade_use_case),
) -> AddReferenceUseCase:
    return AddReferenceUseCase(references, standings, uow, recompute_grade)


def get_list_my_references_use_case(
    references: SqlAlchemyWorkerReferenceRepository = Depends(get_worker_reference_repository),
) -> ListMyReferencesUseCase:
    return ListMyReferencesUseCase(references)


def get_vouch_for_worker_use_case(
    persons: SqlAlchemyPersonRepository = Depends(get_person_repository),
    standings: SqlAlchemyStandingRepository = Depends(get_standing_repository),
    vouches: SqlAlchemyWorkerVouchRepository = Depends(get_worker_vouch_repository),
    uow: SqlAlchemyUnitOfWork = Depends(get_unit_of_work),
    recompute_grade: RecomputeGradeUseCase = Depends(get_recompute_grade_use_case),
) -> VouchForWorkerUseCase:
    return VouchForWorkerUseCase(persons, standings, vouches, uow, recompute_grade)
