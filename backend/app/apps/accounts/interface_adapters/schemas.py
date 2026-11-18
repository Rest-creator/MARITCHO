import uuid
from datetime import datetime

from pydantic import BaseModel, Field, field_validator, model_validator

from app.shared_kernel.enums import RoleEnum
from app.shared_kernel.text import strip_tags


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: uuid.UUID
    phone: str
    # Active mode (navigation, home screen).
    role: RoleEnum
    # Every side this account can use (always includes `role`).
    roles: list[RoleEnum] = Field(default_factory=list)
    display_name: str | None = None
    is_available: bool = True
    travel_km: int = 50
    home_suburb: str | None = None
    next_of_kin_phone: str | None = None
    created_at: datetime | None = None

    @model_validator(mode="after")
    def include_active_role(self) -> "UserOut":
        self.roles = sorted({*self.roles, self.role}, key=lambda role: role.value)
        return self


class UserProfilePatch(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=100)
    is_available: bool | None = None
    travel_km: int | None = Field(default=None, ge=1, le=50)
    home_suburb: str | None = Field(default=None, min_length=1, max_length=100)
    next_of_kin_phone: str | None = Field(default=None, max_length=20)
    role: RoleEnum | None = None

    @field_validator("display_name", "home_suburb", "next_of_kin_phone")
    @classmethod
    def sanitize_profile_text(cls, value: str | None) -> str | None:
        return strip_tags(value) if value is not None else value


class SignUpIn(BaseModel):
    phone: str = Field(min_length=7, max_length=20)
    # 72 bytes is bcrypt's own hard limit.
    password: str = Field(min_length=8, max_length=72)
    name: str = Field(min_length=2, max_length=100)
    role: RoleEnum = RoleEnum.BUYER

    @field_validator("name")
    @classmethod
    def sanitize_name(cls, value: str) -> str:
        return strip_tags(value)


class SignInIn(BaseModel):
    phone: str = Field(min_length=7, max_length=20)
    password: str = Field(min_length=8, max_length=72)
