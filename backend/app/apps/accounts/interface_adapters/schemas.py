import uuid

from pydantic import BaseModel, Field, field_validator

from app.shared_kernel.enums import RoleEnum
from app.shared_kernel.text import strip_tags


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: uuid.UUID
    phone: str
    role: RoleEnum
    display_name: str | None = None
    is_available: bool = True
    travel_km: int = 50
    home_suburb: str | None = None


class UserProfilePatch(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=100)
    is_available: bool | None = None
    travel_km: int | None = Field(default=None, ge=1, le=50)
    home_suburb: str | None = Field(default=None, min_length=1, max_length=100)

    @field_validator("display_name", "home_suburb")
    @classmethod
    def sanitize_profile_text(cls, value: str | None) -> str | None:
        return strip_tags(value) if value is not None else value


class OTPRequestIn(BaseModel):
    phone: str = Field(min_length=7, max_length=20)


class OTPVerifyIn(BaseModel):
    phone: str = Field(min_length=7, max_length=20)
    code: str = Field(min_length=4, max_length=8)
    role: RoleEnum = RoleEnum.BUYER
