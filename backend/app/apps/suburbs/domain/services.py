from collections.abc import Sequence

from app.apps.suburbs.domain.entities import Suburb
from app.apps.suburbs.domain.repositories import SuburbRepository


class ListSuburbsUseCase:
    """Public reference data: known suburbs and their centroids, for building
    a suburb picker (icons/list) client-side rather than free-text entry."""

    def __init__(self, suburbs: SuburbRepository) -> None:
        self._suburbs = suburbs

    async def execute(self, *, limit: int, offset: int) -> Sequence[Suburb]:
        return await self._suburbs.list(limit=limit, offset=offset)
