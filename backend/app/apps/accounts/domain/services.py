from app.apps.accounts.domain.entities import Person
from app.apps.accounts.domain.repositories import PersonRepository
from app.shared_kernel.enums import RoleEnum
from app.shared_kernel.unit_of_work import UnitOfWork


class GetOrCreatePersonByPhoneUseCase:
    """Mock login: find a Person by phone, or create one. In production
    this would be replaced by WhatsApp OTP verification (see
    docs/backlog.md BACK-009) — this stand-in is unchanged from the
    original main.py::login_for_access_token except for accepting a role
    at creation time (the mobile app's role picker)."""

    def __init__(self, persons: PersonRepository, uow: UnitOfWork) -> None:
        self._persons = persons
        self._uow = uow

    async def execute(self, phone: str, role: RoleEnum = RoleEnum.BUYER) -> Person:
        person = await self._persons.get_by_phone(phone)
        if person is not None:
            # An existing account's role is authoritative — a later login
            # carrying a different role (e.g. a stale client) never changes it.
            return person
        person = await self._persons.create(phone=phone, role=role)
        await self._uow.commit()
        return person
