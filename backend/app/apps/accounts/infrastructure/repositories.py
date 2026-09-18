import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.apps.accounts.domain.entities import Person
from app.apps.accounts.domain.repositories import PersonRepository
from app.apps.accounts.infrastructure.models import PersonModel
from app.shared_kernel.enums import RoleEnum


def _to_entity(model: PersonModel) -> Person:
    return Person(
        id=model.id,
        phone=model.phone,
        role=model.role,
        next_of_kin_phone=model.next_of_kin_phone,
        guarantor_id=model.guarantor_id,
        created_at=model.created_at,
    )


class SqlAlchemyPersonRepository(PersonRepository):
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_by_id(self, person_id: uuid.UUID) -> Person | None:
        model = await self._db.get(PersonModel, person_id)
        return _to_entity(model) if model else None

    async def get_by_phone(self, phone: str) -> Person | None:
        result = await self._db.execute(select(PersonModel).where(PersonModel.phone == phone))
        model = result.scalars().first()
        return _to_entity(model) if model else None

    async def create(self, *, phone: str, role: RoleEnum) -> Person:
        model = PersonModel(phone=phone, role=role)
        self._db.add(model)
        await self._db.flush()
        return _to_entity(model)
