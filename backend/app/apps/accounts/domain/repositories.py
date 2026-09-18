import uuid
from abc import ABC, abstractmethod

from app.apps.accounts.domain.entities import Person
from app.shared_kernel.enums import RoleEnum


class PersonRepository(ABC):
    @abstractmethod
    async def get_by_id(self, person_id: uuid.UUID) -> Person | None: ...

    @abstractmethod
    async def get_by_phone(self, phone: str) -> Person | None: ...

    @abstractmethod
    async def create(self, *, phone: str, role: RoleEnum) -> Person:
        """Stages the new row (add + flush) but does not commit — the
        calling use case commits once via UnitOfWork."""
