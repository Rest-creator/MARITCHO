import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.apps.accounts.domain.entities import Person
from app.apps.accounts.domain.repositories import PersonRepository
from app.apps.accounts.infrastructure.models import PersonModel
from app.shared_kernel.enums import RoleEnum


def person_from_model(model: PersonModel) -> Person:
    return Person(
        id=model.id,
        phone=model.phone,
        role=model.role,
        next_of_kin_phone=model.next_of_kin_phone,
        guarantor_id=model.guarantor_id,
        created_at=model.created_at,
        display_name=model.display_name,
        is_available=model.is_available,
        travel_km=model.travel_km,
        home_suburb=model.home_suburb,
        password_hash=model.password_hash,
        roles=_roles_from_storage(model.roles),
    )


def _roles_from_storage(values: list[str] | None) -> frozenset[RoleEnum]:
    known = {role.value for role in RoleEnum}
    return frozenset(RoleEnum(value) for value in (values or []) if value in known)


def _roles_for_storage(person: Person) -> list[str]:
    return sorted(role.value for role in person.capabilities)


class SqlAlchemyPersonRepository(PersonRepository):
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_by_id(self, person_id: uuid.UUID) -> Person | None:
        model = await self._db.get(PersonModel, person_id)
        return person_from_model(model) if model else None

    async def get_by_phone(self, phone: str) -> Person | None:
        result = await self._db.execute(select(PersonModel).where(PersonModel.phone == phone))
        model = result.scalars().first()
        return person_from_model(model) if model else None

    async def update(self, person: Person) -> None:
        model = await self._db.get(PersonModel, person.id)
        if model is None:
            return
        model.role = person.role
        model.roles = _roles_for_storage(person)
        model.display_name = person.display_name
        model.is_available = person.is_available
        model.travel_km = person.travel_km
        model.home_suburb = person.home_suburb
        model.next_of_kin_phone = person.next_of_kin_phone
        await self._db.commit()

    async def create(
        self,
        *,
        phone: str,
        role: RoleEnum,
        password_hash: str | None = None,
        display_name: str | None = None,
    ) -> Person:
        model = PersonModel(
            phone=phone,
            role=role,
            roles=[role.value],
            password_hash=password_hash,
            display_name=display_name,
        )
        self._db.add(model)
        await self._db.flush()
        return person_from_model(model)
