from app.apps.accounts.domain.entities import Person
from app.apps.accounts.domain.repositories import PersonRepository
from app.shared_kernel.enums import RoleEnum
from app.shared_kernel.unit_of_work import UnitOfWork


class GetOrCreatePersonByPhoneUseCase:
    """Mock login: find a Person by phone, or create one defaulting to
    BUYER. In production this would be replaced by WhatsApp OTP
    verification (see docs/backlog.md BACK-009) — this stand-in is
    unchanged from the original main.py::login_for_access_token."""

    def __init__(self, persons: PersonRepository, uow: UnitOfWork) -> None:
        self._persons = persons
        self._uow = uow

    async def execute(self, phone: str) -> Person:
        person = await self._persons.get_by_phone(phone)
        if person is not None:
            return person
        person = await self._persons.create(phone=phone, role=RoleEnum.BUYER)
        await self._uow.commit()
        return person
