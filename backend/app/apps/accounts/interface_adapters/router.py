from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.apps.accounts.domain.entities import Person
from app.apps.accounts.domain.repositories import PersonRepository
from app.apps.accounts.domain.services import SignInUseCase, SignUpUseCase
from app.apps.accounts.interface_adapters.dependencies import (
    get_current_user,
    get_person_repository,
    get_sign_in_use_case,
    get_sign_up_use_case,
)
from app.apps.accounts.interface_adapters.schemas import (
    SignInIn,
    SignUpIn,
    TokenOut,
    UserOut,
    UserProfilePatch,
)
from app.apps.suburbs.infrastructure.models import SuburbModel
from app.core.database import get_db_session
from app.core.security import create_access_token
from app.shared_kernel.enums import RoleEnum

router = APIRouter(tags=["accounts"])


@router.post("/auth/signup", response_model=TokenOut)
async def sign_up(
    payload: SignUpIn,
    use_case: SignUpUseCase = Depends(get_sign_up_use_case),
) -> dict[str, str]:
    person = await use_case.execute(payload.phone, payload.password, payload.name, payload.role)
    return {"access_token": create_access_token(data={"sub": person.phone}), "token_type": "bearer"}


@router.post("/auth/signin", response_model=TokenOut)
async def sign_in(
    payload: SignInIn,
    use_case: SignInUseCase = Depends(get_sign_in_use_case),
) -> dict[str, str]:
    person = await use_case.execute(payload.phone, payload.password)
    return {"access_token": create_access_token(data={"sub": person.phone}), "token_type": "bearer"}


@router.get("/users/me", response_model=UserOut)
async def read_users_me(current_user: Person = Depends(get_current_user)) -> Person:
    return current_user


@router.patch("/users/me", response_model=UserOut)
async def update_users_me(
    payload: UserProfilePatch,
    current_user: Person = Depends(get_current_user),
    persons: PersonRepository = Depends(get_person_repository),
    db: AsyncSession = Depends(get_db_session),
) -> Person:
    values = payload.model_dump(exclude_unset=True)
    if (
        values.get("home_suburb") is not None
        and await db.get(SuburbModel, values["home_suburb"]) is None
    ):
        from fastapi import HTTPException

        raise HTTPException(status_code=422, detail="Unknown home suburb")
    if "display_name" in values:
        current_user.display_name = values["display_name"]
    for key in ("is_available", "travel_km", "home_suburb"):
        if key in values:
            if current_user.role != RoleEnum.WORKER:
                continue
            setattr(current_user, key, values[key])
    await persons.update(current_user)
    return current_user
