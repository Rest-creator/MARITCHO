from fastapi import Depends
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.exceptions import IntegrityConflictError
from app.shared_kernel.unit_of_work import UnitOfWork


class SqlAlchemyUnitOfWork(UnitOfWork):
    """Wraps the request's AsyncSession — constructed with the *same*
    session instance passed to that request's repositories, so commit/
    rollback apply to the same transaction they wrote to."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def commit(self) -> None:
        try:
            await self._db.commit()
        except IntegrityError as exc:
            await self._db.rollback()
            raise IntegrityConflictError(str(exc)) from exc

    async def rollback(self) -> None:
        await self._db.rollback()


def get_unit_of_work(db: AsyncSession = Depends(get_db_session)) -> SqlAlchemyUnitOfWork:
    """Shared FastAPI dependency factory — every app's use-case factories
    import this rather than redefining it. FastAPI caches `get_db_session`
    per request, so this shares the same session/transaction as any
    repository built from the same request's `Depends(get_db_session)`."""
    return SqlAlchemyUnitOfWork(db)
