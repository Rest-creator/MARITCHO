import os

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
    GetWorkerPublicProfileUseCase,
    ListMyReferencesUseCase,
    ListMyServiceAreasUseCase,
    ListMySkillsUseCase,
    ListNearbyWorkersUseCase,
    ListPendingVettingUseCase,
    RecomputeGradeUseCase,
    RegisterServiceAreaUseCase,
    RegisterSkillUseCase,
    ReviewIdDocumentUseCase,
    ReviewPoliceClearanceUseCase,
    SubmitIdPhotoUseCase,
    SubmitPoliceClearanceUseCase,
    VouchForWorkerUseCase,
)
from app.apps.workers.infrastructure.repositories import (
    SqlAlchemyMediaOwnershipRepository,
    SqlAlchemyServiceAreaRepository,
    SqlAlchemySkillRepository,
    SqlAlchemyStandingRepository,
    SqlAlchemyWorkerDirectoryRepository,
    SqlAlchemyWorkerReferenceRepository,
    SqlAlchemyWorkerVettingRepository,
    SqlAlchemyWorkerVouchRepository,
)
from app.core.database import get_db_session
from app.core.security import SECRET_KEY
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


def get_media_ownership_repository(
    db: AsyncSession = Depends(get_db_session),
) -> SqlAlchemyMediaOwnershipRepository:
    return SqlAlchemyMediaOwnershipRepository(db)


def get_id_number_hash_key() -> bytes:
    """HMAC key for national ID numbers (ADR-010). Set ID_NUMBER_HASH_KEY in
    production and never rotate it casually: a new key makes old hashes
    unmatchable, so duplicate-ID detection would miss earlier accounts."""
    return os.getenv("ID_NUMBER_HASH_KEY", SECRET_KEY).encode("utf-8")


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
    media: SqlAlchemyMediaOwnershipRepository = Depends(get_media_ownership_repository),
) -> SubmitIdPhotoUseCase:
    return SubmitIdPhotoUseCase(vetting, standings, uow, recompute_grade, view, media)


def get_submit_police_clearance_use_case(
    vetting: SqlAlchemyWorkerVettingRepository = Depends(get_worker_vetting_repository),
    standings: SqlAlchemyStandingRepository = Depends(get_standing_repository),
    uow: SqlAlchemyUnitOfWork = Depends(get_unit_of_work),
    recompute_grade: RecomputeGradeUseCase = Depends(get_recompute_grade_use_case),
    view: GetVettingViewUseCase = Depends(get_vetting_view_use_case),
    media: SqlAlchemyMediaOwnershipRepository = Depends(get_media_ownership_repository),
) -> SubmitPoliceClearanceUseCase:
    return SubmitPoliceClearanceUseCase(vetting, standings, uow, recompute_grade, view, media)


def get_list_pending_vetting_use_case(
    vetting: SqlAlchemyWorkerVettingRepository = Depends(get_worker_vetting_repository),
) -> ListPendingVettingUseCase:
    return ListPendingVettingUseCase(vetting)


def get_review_id_document_use_case(
    vetting: SqlAlchemyWorkerVettingRepository = Depends(get_worker_vetting_repository),
    standings: SqlAlchemyStandingRepository = Depends(get_standing_repository),
    uow: SqlAlchemyUnitOfWork = Depends(get_unit_of_work),
    recompute_grade: RecomputeGradeUseCase = Depends(get_recompute_grade_use_case),
    view: GetVettingViewUseCase = Depends(get_vetting_view_use_case),
    key: bytes = Depends(get_id_number_hash_key),
) -> ReviewIdDocumentUseCase:
    return ReviewIdDocumentUseCase(vetting, standings, uow, recompute_grade, view, key)


def get_review_police_clearance_use_case(
    vetting: SqlAlchemyWorkerVettingRepository = Depends(get_worker_vetting_repository),
    uow: SqlAlchemyUnitOfWork = Depends(get_unit_of_work),
    view: GetVettingViewUseCase = Depends(get_vetting_view_use_case),
) -> ReviewPoliceClearanceUseCase:
    return ReviewPoliceClearanceUseCase(vetting, uow, view)


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


def get_worker_directory_repository(
    db: AsyncSession = Depends(get_db_session),
) -> SqlAlchemyWorkerDirectoryRepository:
    return SqlAlchemyWorkerDirectoryRepository(db)


def get_list_nearby_workers_use_case(
    directory: SqlAlchemyWorkerDirectoryRepository = Depends(get_worker_directory_repository),
    suburbs: SqlAlchemySuburbRepository = Depends(get_suburb_repository),
) -> ListNearbyWorkersUseCase:
    return ListNearbyWorkersUseCase(directory, suburbs)


def get_worker_public_profile_use_case(
    directory: SqlAlchemyWorkerDirectoryRepository = Depends(get_worker_directory_repository),
    suburbs: SqlAlchemySuburbRepository = Depends(get_suburb_repository),
) -> GetWorkerPublicProfileUseCase:
    return GetWorkerPublicProfileUseCase(directory, suburbs)

