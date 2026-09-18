from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.apps.accounts.infrastructure.repositories import SqlAlchemyPersonRepository
from app.apps.accounts.interface_adapters.dependencies import get_person_repository
from app.apps.crews.domain.matching import CrewMatchingService
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
from app.apps.crews.infrastructure.repositories import (
    SqlAlchemyCrewMemberRepository,
    SqlAlchemyCrewOrderLedgerEntryRepository,
    SqlAlchemyCrewOrderRepository,
    SqlAlchemyCrewRepository,
)
from app.apps.jobs.interface_adapters.dependencies import get_job_repository
from app.apps.payments.infrastructure.ecocash_gateway import EcoCashGateway
from app.apps.payments.interface_adapters.dependencies import get_ecocash_gateway
from app.apps.suburbs.infrastructure.repositories import SqlAlchemySuburbRepository
from app.apps.suburbs.interface_adapters.dependencies import get_suburb_repository
from app.apps.workers.infrastructure.matching_profile_adapter import WorkerMatchingProfileAdapter
from app.core.database import get_db_session
from app.core.unit_of_work import SqlAlchemyUnitOfWork, get_unit_of_work


def get_crew_repository(db: AsyncSession = Depends(get_db_session)) -> SqlAlchemyCrewRepository:
    return SqlAlchemyCrewRepository(db)


def get_crew_member_repository(
    db: AsyncSession = Depends(get_db_session),
) -> SqlAlchemyCrewMemberRepository:
    return SqlAlchemyCrewMemberRepository(db)


def get_crew_order_repository(
    db: AsyncSession = Depends(get_db_session),
) -> SqlAlchemyCrewOrderRepository:
    return SqlAlchemyCrewOrderRepository(db)


def get_crew_order_ledger_entry_repository(
    db: AsyncSession = Depends(get_db_session),
) -> SqlAlchemyCrewOrderLedgerEntryRepository:
    return SqlAlchemyCrewOrderLedgerEntryRepository(db)


def get_worker_matching_profile_port(
    db: AsyncSession = Depends(get_db_session),
) -> WorkerMatchingProfileAdapter:
    return WorkerMatchingProfileAdapter(db)


def get_crew_matching_service(
    crews: SqlAlchemyCrewRepository = Depends(get_crew_repository),
    crew_members: SqlAlchemyCrewMemberRepository = Depends(get_crew_member_repository),
    crew_orders: SqlAlchemyCrewOrderRepository = Depends(get_crew_order_repository),
    worker_profiles: WorkerMatchingProfileAdapter = Depends(get_worker_matching_profile_port),
    db: AsyncSession = Depends(get_db_session),
    suburbs: SqlAlchemySuburbRepository = Depends(get_suburb_repository),
) -> CrewMatchingService:
    worker_availability = get_job_repository(db)
    return CrewMatchingService(
        crews, crew_members, crew_orders, worker_profiles, worker_availability, suburbs
    )


def get_create_crew_use_case(
    crews: SqlAlchemyCrewRepository = Depends(get_crew_repository),
    uow: SqlAlchemyUnitOfWork = Depends(get_unit_of_work),
) -> CreateCrewUseCase:
    return CreateCrewUseCase(crews, uow)


def get_get_own_crew_use_case(
    crews: SqlAlchemyCrewRepository = Depends(get_crew_repository),
    members: SqlAlchemyCrewMemberRepository = Depends(get_crew_member_repository),
) -> GetOwnCrewUseCase:
    return GetOwnCrewUseCase(crews, members)


def get_add_crew_member_use_case(
    crews: SqlAlchemyCrewRepository = Depends(get_crew_repository),
    members: SqlAlchemyCrewMemberRepository = Depends(get_crew_member_repository),
    persons: SqlAlchemyPersonRepository = Depends(get_person_repository),
    uow: SqlAlchemyUnitOfWork = Depends(get_unit_of_work),
) -> AddCrewMemberUseCase:
    return AddCrewMemberUseCase(crews, members, persons, uow)


def get_remove_crew_member_use_case(
    crews: SqlAlchemyCrewRepository = Depends(get_crew_repository),
    members: SqlAlchemyCrewMemberRepository = Depends(get_crew_member_repository),
    uow: SqlAlchemyUnitOfWork = Depends(get_unit_of_work),
) -> RemoveCrewMemberUseCase:
    return RemoveCrewMemberUseCase(crews, members, uow)


def get_create_crew_order_use_case(
    orders: SqlAlchemyCrewOrderRepository = Depends(get_crew_order_repository),
    suburbs: SqlAlchemySuburbRepository = Depends(get_suburb_repository),
    uow: SqlAlchemyUnitOfWork = Depends(get_unit_of_work),
) -> CreateCrewOrderUseCase:
    return CreateCrewOrderUseCase(orders, suburbs, uow)


def get_get_crew_order_use_case(
    orders: SqlAlchemyCrewOrderRepository = Depends(get_crew_order_repository),
    crews: SqlAlchemyCrewRepository = Depends(get_crew_repository),
) -> GetCrewOrderUseCase:
    return GetCrewOrderUseCase(orders, crews)


def get_get_crew_order_matches_use_case(
    orders: SqlAlchemyCrewOrderRepository = Depends(get_crew_order_repository),
    matching: CrewMatchingService = Depends(get_crew_matching_service),
    uow: SqlAlchemyUnitOfWork = Depends(get_unit_of_work),
) -> GetCrewOrderMatchesUseCase:
    return GetCrewOrderMatchesUseCase(orders, matching, uow)


def get_book_crew_order_use_case(
    orders: SqlAlchemyCrewOrderRepository = Depends(get_crew_order_repository),
    crews: SqlAlchemyCrewRepository = Depends(get_crew_repository),
    ledger: SqlAlchemyCrewOrderLedgerEntryRepository = Depends(
        get_crew_order_ledger_entry_repository
    ),
    payment_gateway: EcoCashGateway = Depends(get_ecocash_gateway),
    uow: SqlAlchemyUnitOfWork = Depends(get_unit_of_work),
) -> BookCrewOrderUseCase:
    return BookCrewOrderUseCase(orders, crews, ledger, payment_gateway, uow)


def get_submit_crew_order_quote_use_case(
    orders: SqlAlchemyCrewOrderRepository = Depends(get_crew_order_repository),
    crews: SqlAlchemyCrewRepository = Depends(get_crew_repository),
    ledger: SqlAlchemyCrewOrderLedgerEntryRepository = Depends(
        get_crew_order_ledger_entry_repository
    ),
    uow: SqlAlchemyUnitOfWork = Depends(get_unit_of_work),
) -> SubmitCrewOrderQuoteUseCase:
    return SubmitCrewOrderQuoteUseCase(orders, crews, ledger, uow)


def get_complete_crew_order_use_case(
    orders: SqlAlchemyCrewOrderRepository = Depends(get_crew_order_repository),
    ledger: SqlAlchemyCrewOrderLedgerEntryRepository = Depends(
        get_crew_order_ledger_entry_repository
    ),
    uow: SqlAlchemyUnitOfWork = Depends(get_unit_of_work),
) -> CompleteCrewOrderUseCase:
    return CompleteCrewOrderUseCase(orders, ledger, uow)


def get_get_crew_order_ledger_use_case(
    orders: SqlAlchemyCrewOrderRepository = Depends(get_crew_order_repository),
    crews: SqlAlchemyCrewRepository = Depends(get_crew_repository),
    ledger: SqlAlchemyCrewOrderLedgerEntryRepository = Depends(
        get_crew_order_ledger_entry_repository
    ),
) -> GetCrewOrderLedgerUseCase:
    return GetCrewOrderLedgerUseCase(orders, crews, ledger)
