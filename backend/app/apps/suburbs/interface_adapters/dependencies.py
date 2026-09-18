from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.apps.suburbs.domain.services import ListSuburbsUseCase
from app.apps.suburbs.infrastructure.repositories import SqlAlchemySuburbRepository
from app.core.database import get_db_session


def get_suburb_repository(
    db: AsyncSession = Depends(get_db_session),
) -> SqlAlchemySuburbRepository:
    """Also satisfies shared_kernel.ports.SuburbLookupPort — other apps'
    dependency factories construct this same class when they need suburb
    lookups (see apps/jobs, apps/crews)."""
    return SqlAlchemySuburbRepository(db)


def get_list_suburbs_use_case(
    suburbs: SqlAlchemySuburbRepository = Depends(get_suburb_repository),
) -> ListSuburbsUseCase:
    return ListSuburbsUseCase(suburbs)
