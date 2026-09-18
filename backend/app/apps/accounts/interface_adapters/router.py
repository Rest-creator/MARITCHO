from typing import Any

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from app.apps.accounts.domain.entities import Person
from app.apps.accounts.domain.services import GetOrCreatePersonByPhoneUseCase
from app.apps.accounts.interface_adapters.dependencies import get_current_user, get_login_use_case
from app.apps.accounts.interface_adapters.schemas import TokenOut, UserOut
from app.core.security import create_access_token

router = APIRouter(tags=["accounts"])


@router.post("/token", response_model=TokenOut)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    use_case: GetOrCreatePersonByPhoneUseCase = Depends(get_login_use_case),
) -> dict[str, Any]:
    """Mock login endpoint for development.

    In production, this would use WhatsApp OTP verification.
    """
    person = await use_case.execute(form_data.username)
    access_token = create_access_token(data={"sub": person.phone})
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/users/me", response_model=UserOut)
async def read_users_me(current_user: Person = Depends(get_current_user)) -> Person:
    return current_user
