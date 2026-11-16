from fastapi import HTTPException, status

from app.apps.accounts.domain.entities import Person
from app.apps.accounts.domain.repositories import PersonRepository
from app.core.security import hash_password, verify_password
from app.shared_kernel.enums import RoleEnum
from app.shared_kernel.unit_of_work import UnitOfWork


class SignUpUseCase:
    """Create a new account with a phone number and password. Rejects a
    phone that's already registered — use SignInUseCase for that."""

    def __init__(self, persons: PersonRepository, uow: UnitOfWork) -> None:
        self._persons = persons
        self._uow = uow

    async def execute(self, phone: str, password: str, name: str, role: RoleEnum) -> Person:
        existing = await self._persons.get_by_phone(phone)
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this phone number already exists.",
            )
        person = await self._persons.create(
            phone=phone,
            role=role,
            password_hash=hash_password(password),
            display_name=name,
        )
        await self._uow.commit()
        return person


class SignInUseCase:
    """Verify a phone + password against an existing account."""

    def __init__(self, persons: PersonRepository) -> None:
        self._persons = persons

    async def execute(self, phone: str, password: str) -> Person:
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect phone number or password.",
        )
        person = await self._persons.get_by_phone(phone)
        if person is None or not person.password_hash:
            raise credentials_exception
        if not verify_password(password, person.password_hash):
            raise credentials_exception
        return person
