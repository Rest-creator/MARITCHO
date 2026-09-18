from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.apps.accounts.infrastructure.repositories import SqlAlchemyPersonRepository
from app.apps.accounts.interface_adapters.dependencies import get_person_repository
from app.apps.jobs.domain.matching import JobMatchingService
from app.apps.jobs.domain.services import (
    BookJobUseCase,
    CompleteJobUseCase,
    CreateJobRequestUseCase,
    GetJobLedgerUseCase,
    GetJobMatchesUseCase,
    GetJobRecordUseCase,
    GetJobUseCase,
    ListJobDisputesUseCase,
    RaiseDisputeUseCase,
    RespondToDisputeUseCase,
    SubmitQuoteUseCase,
)
from app.apps.jobs.infrastructure.repositories import (
    SqlAlchemyDisputeRepository,
    SqlAlchemyJobRepository,
    SqlAlchemyLedgerEntryRepository,
    SqlAlchemyRecordEntryRepository,
)
from app.apps.jobs.infrastructure.worker_job_stats_adapter import WorkerJobStatsAdapter
from app.apps.payments.infrastructure.ecocash_gateway import EcoCashGateway
from app.apps.payments.interface_adapters.dependencies import get_ecocash_gateway
from app.apps.suburbs.infrastructure.repositories import SqlAlchemySuburbRepository
from app.apps.suburbs.interface_adapters.dependencies import get_suburb_repository
from app.apps.workers.domain.services import RecomputeStandingUseCase
from app.apps.workers.infrastructure.matching_profile_adapter import WorkerMatchingProfileAdapter
from app.apps.workers.interface_adapters.dependencies import get_standing_repository
from app.core.database import get_db_session
from app.core.unit_of_work import SqlAlchemyUnitOfWork, get_unit_of_work


def get_job_repository(db: AsyncSession = Depends(get_db_session)) -> SqlAlchemyJobRepository:
    """Also satisfies shared_kernel.ports.WorkerAvailabilityPort — the
    workers app's standing endpoint and the crews app's matching service
    both build this same class when they need worker-busy/dispute checks."""
    return SqlAlchemyJobRepository(db)


def get_ledger_entry_repository(
    db: AsyncSession = Depends(get_db_session),
) -> SqlAlchemyLedgerEntryRepository:
    return SqlAlchemyLedgerEntryRepository(db)


def get_dispute_repository(
    db: AsyncSession = Depends(get_db_session),
) -> SqlAlchemyDisputeRepository:
    return SqlAlchemyDisputeRepository(db)


def get_record_entry_repository(
    db: AsyncSession = Depends(get_db_session),
) -> SqlAlchemyRecordEntryRepository:
    return SqlAlchemyRecordEntryRepository(db)


def get_worker_matching_profile_port(
    db: AsyncSession = Depends(get_db_session),
) -> WorkerMatchingProfileAdapter:
    return WorkerMatchingProfileAdapter(db)


def get_job_matching_service(
    jobs: SqlAlchemyJobRepository = Depends(get_job_repository),
    worker_profiles: WorkerMatchingProfileAdapter = Depends(get_worker_matching_profile_port),
    suburbs: SqlAlchemySuburbRepository = Depends(get_suburb_repository),
) -> JobMatchingService:
    return JobMatchingService(jobs, worker_profiles, suburbs)


def get_recompute_worker_standing_use_case(
    db: AsyncSession = Depends(get_db_session),
) -> RecomputeStandingUseCase:
    """Constructs the workers app's own use case directly — workers is a
    foundational direct dependency for jobs (same pattern as jobs' own
    direct use of accounts.PersonRepository), not a new shared_kernel
    port. `WorkerJobStatsAdapter` is this app's own implementation of
    WorkerJobStatsPort, which the workers use case takes as a dependency."""
    standings = get_standing_repository(db)
    job_stats = WorkerJobStatsAdapter(db)
    return RecomputeStandingUseCase(standings, job_stats)


def get_create_job_request_use_case(
    jobs: SqlAlchemyJobRepository = Depends(get_job_repository),
    suburbs: SqlAlchemySuburbRepository = Depends(get_suburb_repository),
    uow: SqlAlchemyUnitOfWork = Depends(get_unit_of_work),
) -> CreateJobRequestUseCase:
    return CreateJobRequestUseCase(jobs, suburbs, uow)


def get_get_job_use_case(
    jobs: SqlAlchemyJobRepository = Depends(get_job_repository),
) -> GetJobUseCase:
    return GetJobUseCase(jobs)


def get_get_job_matches_use_case(
    jobs: SqlAlchemyJobRepository = Depends(get_job_repository),
    matching: JobMatchingService = Depends(get_job_matching_service),
    uow: SqlAlchemyUnitOfWork = Depends(get_unit_of_work),
) -> GetJobMatchesUseCase:
    return GetJobMatchesUseCase(jobs, matching, uow)


def get_book_job_use_case(
    jobs: SqlAlchemyJobRepository = Depends(get_job_repository),
    persons: SqlAlchemyPersonRepository = Depends(get_person_repository),
    worker_profiles: WorkerMatchingProfileAdapter = Depends(get_worker_matching_profile_port),
    ledger: SqlAlchemyLedgerEntryRepository = Depends(get_ledger_entry_repository),
    payment_gateway: EcoCashGateway = Depends(get_ecocash_gateway),
    uow: SqlAlchemyUnitOfWork = Depends(get_unit_of_work),
) -> BookJobUseCase:
    return BookJobUseCase(jobs, persons, worker_profiles, ledger, payment_gateway, uow)


def get_submit_quote_use_case(
    jobs: SqlAlchemyJobRepository = Depends(get_job_repository),
    ledger: SqlAlchemyLedgerEntryRepository = Depends(get_ledger_entry_repository),
    uow: SqlAlchemyUnitOfWork = Depends(get_unit_of_work),
) -> SubmitQuoteUseCase:
    return SubmitQuoteUseCase(jobs, ledger, uow)


def get_complete_job_use_case(
    jobs: SqlAlchemyJobRepository = Depends(get_job_repository),
    records: SqlAlchemyRecordEntryRepository = Depends(get_record_entry_repository),
    ledger: SqlAlchemyLedgerEntryRepository = Depends(get_ledger_entry_repository),
    recompute_standing: RecomputeStandingUseCase = Depends(get_recompute_worker_standing_use_case),
    uow: SqlAlchemyUnitOfWork = Depends(get_unit_of_work),
) -> CompleteJobUseCase:
    return CompleteJobUseCase(jobs, records, ledger, recompute_standing, uow)


def get_raise_dispute_use_case(
    jobs: SqlAlchemyJobRepository = Depends(get_job_repository),
    disputes: SqlAlchemyDisputeRepository = Depends(get_dispute_repository),
    recompute_standing: RecomputeStandingUseCase = Depends(get_recompute_worker_standing_use_case),
    uow: SqlAlchemyUnitOfWork = Depends(get_unit_of_work),
) -> RaiseDisputeUseCase:
    return RaiseDisputeUseCase(jobs, disputes, recompute_standing, uow)


def get_respond_to_dispute_use_case(
    jobs: SqlAlchemyJobRepository = Depends(get_job_repository),
    disputes: SqlAlchemyDisputeRepository = Depends(get_dispute_repository),
    uow: SqlAlchemyUnitOfWork = Depends(get_unit_of_work),
) -> RespondToDisputeUseCase:
    return RespondToDisputeUseCase(jobs, disputes, uow)


def get_list_job_disputes_use_case(
    jobs: SqlAlchemyJobRepository = Depends(get_job_repository),
    disputes: SqlAlchemyDisputeRepository = Depends(get_dispute_repository),
) -> ListJobDisputesUseCase:
    return ListJobDisputesUseCase(jobs, disputes)


def get_get_job_ledger_use_case(
    jobs: SqlAlchemyJobRepository = Depends(get_job_repository),
    ledger: SqlAlchemyLedgerEntryRepository = Depends(get_ledger_entry_repository),
) -> GetJobLedgerUseCase:
    return GetJobLedgerUseCase(jobs, ledger)


def get_get_job_record_use_case(
    jobs: SqlAlchemyJobRepository = Depends(get_job_repository),
    records: SqlAlchemyRecordEntryRepository = Depends(get_record_entry_repository),
) -> GetJobRecordUseCase:
    return GetJobRecordUseCase(jobs, records)
