from collections.abc import Sequence
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.apps.suburbs.domain.entities import Suburb
from app.apps.suburbs.domain.repositories import SuburbRepository
from app.apps.suburbs.infrastructure.models import SuburbModel
from app.shared_kernel.ports import SuburbLookupPort


def _to_entity(model: SuburbModel) -> Suburb:
    return Suburb(name=model.name, latitude=model.latitude, longitude=model.longitude)


class SqlAlchemySuburbRepository(SuburbRepository, SuburbLookupPort):
    """Implements both the app's own repository interface and the
    shared_kernel port other apps consume (ADR-007) — one concrete class,
    two contracts, wired to whichever apps need it at the composition root.
    """

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def list(self, *, limit: int, offset: int) -> Sequence[Suburb]:
        result = await self._db.execute(
            select(SuburbModel).order_by(SuburbModel.name).limit(limit).offset(offset)
        )
        return [_to_entity(model) for model in result.scalars().all()]

    async def exists(self, name: str) -> bool:
        return await self._db.get(SuburbModel, name) is not None

    async def get_coords(self, names: set[str]) -> dict[str, tuple[Decimal, Decimal]]:
        result = await self._db.execute(select(SuburbModel).where(SuburbModel.name.in_(names)))
        return {model.name: (model.latitude, model.longitude) for model in result.scalars().all()}
