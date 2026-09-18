"""Identity resolution and role-gating — imported by every other app's
router (`Depends(get_current_user)`, `Depends(RequireRole([...]))`).

This is the one deliberate exception to "apps don't import each other's
interface_adapters": every app legitimately depends on accounts for
identity, exactly like they depend on shared_kernel — see ADR-007.
"""

import jwt
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.apps.accounts.domain.entities import Person
from app.apps.accounts.domain.services import GetOrCreatePersonByPhoneUseCase
from app.apps.accounts.infrastructure.repositories import SqlAlchemyPersonRepository
from app.core.database import get_db_session
from app.core.security import decode_access_token, oauth2_scheme
from app.core.unit_of_work import SqlAlchemyUnitOfWork, get_unit_of_work
from app.shared_kernel.enums import RoleEnum


def get_person_repository(
    db: AsyncSession = Depends(get_db_session),
) -> SqlAlchemyPersonRepository:
    return SqlAlchemyPersonRepository(db)


def get_login_use_case(
    persons: SqlAlchemyPersonRepository = Depends(get_person_repository),
    uow: SqlAlchemyUnitOfWork = Depends(get_unit_of_work),
) -> GetOrCreatePersonByPhoneUseCase:
    return GetOrCreatePersonByPhoneUseCase(persons, uow)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    persons: SqlAlchemyPersonRepository = Depends(get_person_repository),
) -> Person:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
    except jwt.PyJWTError as exc:
        raise credentials_exception from exc

    phone = payload.get("sub")
    if not isinstance(phone, str):
        raise credentials_exception

    person = await persons.get_by_phone(phone)
    if person is None:
        raise credentials_exception
    return person


class RequireRole:
    def __init__(self, allowed_roles: list[RoleEnum]) -> None:
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: Person = Depends(get_current_user)) -> Person:
        if current_user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Operation not permitted for this role.",
            )
        return current_user
