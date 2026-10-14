import hashlib
import os
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends, Form, Request
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.apps.accounts.domain.entities import Person
from app.apps.accounts.domain.repositories import PersonRepository
from app.apps.accounts.domain.services import GetOrCreatePersonByPhoneUseCase
from app.apps.accounts.infrastructure.otp_models import OTPRequestModel
from app.apps.accounts.interface_adapters.dependencies import (
    get_current_user,
    get_login_use_case,
    get_person_repository,
)
from app.apps.accounts.interface_adapters.schemas import (
    OTPRequestIn,
    OTPVerifyIn,
    TokenOut,
    UserOut,
    UserProfilePatch,
)
from app.apps.suburbs.infrastructure.models import SuburbModel
from app.core.database import get_db_session
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
    if os.getenv("APP_ENV", "development").lower() == "production":
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Not found")
    person = await use_case.execute(username, role)
    access_token = create_access_token(data={"sub": person.phone})
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/otp/request")
async def request_otp(
    payload: OTPRequestIn,
    request: Request,
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    now = datetime.now(timezone.utc)
    since = now - timedelta(minutes=10)
    ip = request.client.host if request.client else "unknown"
    recent = await db.scalar(
        select(OTPRequestModel)
        .where(
            OTPRequestModel.phone == payload.phone,
            OTPRequestModel.created_at >= since,
            OTPRequestModel.verified_at.is_(None),
        )
        .order_by(desc(OTPRequestModel.created_at))
        .limit(1)
    )
    if recent:
        from fastapi import HTTPException

        raise HTTPException(status_code=429, detail="OTP already requested")
    count = await db.scalar(
        select(func.count())
        .select_from(OTPRequestModel)
        .where(OTPRequestModel.ip_address == ip, OTPRequestModel.created_at >= since)
    )
    if count and count >= 5:
        from fastapi import HTTPException

        raise HTTPException(status_code=429, detail="Too many OTP requests")
    code = (
        "123456"
        if os.getenv("APP_ENV", "development").lower() != "production"
        else f"{secrets.randbelow(1000000):06d}"
    )
    row = OTPRequestModel(
        id=uuid.uuid4(),
        phone=payload.phone,
        ip_address=ip,
        code_hash=hashlib.sha256(code.encode()).hexdigest(),
        expires_at=now + timedelta(minutes=5),
        created_at=now,
    )
    db.add(row)
    await db.commit()
    result: dict[str, object] = {"expires_in": 300}
    if os.getenv("APP_ENV", "development").lower() != "production":
        result["dev_code"] = code
    return result


@router.post("/otp/verify", response_model=TokenOut)
async def verify_otp(
    payload: OTPVerifyIn,
    request: Request,
    db: AsyncSession = Depends(get_db_session),
    use_case: GetOrCreatePersonByPhoneUseCase = Depends(get_login_use_case),
) -> dict[str, str]:
    from fastapi import HTTPException

    row = await db.scalar(
        select(OTPRequestModel)
        .where(
            OTPRequestModel.phone == payload.phone,
            OTPRequestModel.verified_at.is_(None),
        )
        .order_by(desc(OTPRequestModel.created_at))
        .limit(1)
    )
    now = datetime.now(timezone.utc)
    if row is None or row.expires_at < now or row.attempts >= 5:
        raise HTTPException(status_code=401, detail="Invalid or expired OTP")
    row.attempts += 1
    if row.code_hash != hashlib.sha256(payload.code.encode()).hexdigest():
        await db.commit()
        raise HTTPException(status_code=401, detail="Invalid or expired OTP")
    row.verified_at = now
    await db.commit()
    person = await use_case.execute(payload.phone, payload.role)
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
