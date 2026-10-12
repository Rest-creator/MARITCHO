from typing import Any

from fastapi import APIRouter, Depends, Form

from app.apps.accounts.domain.entities import Person
from app.apps.accounts.domain.services import GetOrCreatePersonByPhoneUseCase
from app.apps.accounts.interface_adapters.dependencies import get_current_user, get_login_use_case
from app.apps.accounts.interface_adapters.schemas import TokenOut, UserOut
from app.core.security import create_access_token
from app.shared_kernel.enums import RoleEnum

router = APIRouter(tags=["accounts"])


@router.post("/token", response_model=TokenOut)
async def login_for_access_token(
    username: str = Form(),
    password: str = Form(default=""),
    role: RoleEnum = Form(default=RoleEnum.BUYER),
    use_case: GetOrCreatePersonByPhoneUseCase = Depends(get_login_use_case),
) -> dict[str, Any]:
    """Mock login endpoint for development.

    In production, this would use WhatsApp OTP verification. `username` is
    the phone number (OAuth2 password-flow field naming); `password` is
    unused. `role` only takes effect when this phone number doesn't have
    an account yet — an existing account's role never changes via login.

    Declared as explicit Form() fields rather than Depends(
    OAuth2PasswordRequestForm) because mixing that dependency with a
    sibling Form() parameter double-reads the request body stream and
    fails with a spurious 422 ("password" missing) on every request.
    """
    person = await use_case.execute(username, role)
    access_token = create_access_token(data={"sub": person.phone})
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/users/me", response_model=UserOut)
async def read_users_me(current_user: Person = Depends(get_current_user)) -> Person:
    return current_user
