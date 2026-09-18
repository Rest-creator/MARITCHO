from abc import ABC, abstractmethod
from collections.abc import Sequence

from app.apps.suburbs.domain.entities import Suburb


class SuburbRepository(ABC):
    @abstractmethod
    async def list(self, *, limit: int, offset: int) -> Sequence[Suburb]: ...
