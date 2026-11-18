from fastapi import APIRouter, Depends, HTTPException
from opentelemetry import trace
from sqlalchemy.ext.asyncio import AsyncSession

from app.apps.accounts.domain.entities import SELF_SERVICE_ROLES, Person
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
from app.core.telemetry import logger
from app.shared_kernel.enums import RoleEnum

router = APIRouter(tags=["accounts"])
tracer = trace.get_tracer(__name__)


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
    with tracer.start_as_current_span("accounts.update_users_me") as span:
        span.set_attribute("user.id", str(current_user.id))
        values = payload.model_dump(exclude_unset=True)
        if (
            values.get("home_suburb") is not None
            and await db.get(SuburbModel, values["home_suburb"]) is None
        ):
            raise HTTPException(status_code=422, detail="Unknown home suburb")

        if "role" in values and values["role"] is not None:
            target_role = values["role"]
            if (
                target_role not in SELF_SERVICE_ROLES
                or current_user.role not in SELF_SERVICE_ROLES
            ):
                raise HTTPException(
                    status_code=422,
                    detail="Can only switch between BUYER and WORKER roles",
                )
            # Switching mode unlocks the new side and keeps the old one: one
            # account hires and finds work, with both profiles intact.
            current_user.roles = current_user.capabilities | {target_role}
            current_user.role = target_role
            span.set_attribute("user.roles", sorted(r.value for r in current_user.roles))

        if "display_name" in values:
            current_user.display_name = values["display_name"]
        if "home_suburb" in values:
            current_user.home_suburb = values["home_suburb"]
        if "next_of_kin_phone" in values:
            raw_kin = (values["next_of_kin_phone"] or "").strip()
            current_user.next_of_kin_phone = raw_kin if raw_kin else None

        for key in ("is_available", "travel_km"):
            if key in values and values[key] is not None:
                if not current_user.acts_as(RoleEnum.WORKER):
                    continue
                setattr(current_user, key, values[key])

        await persons.update(current_user)
        logger.info(
            f"Updated user profile user_id={current_user.id} "
            f"role={current_user.role.value} fields={sorted(values.keys())}"
        )
        return current_user
