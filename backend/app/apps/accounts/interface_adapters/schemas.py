import uuid

from pydantic import BaseModel

from app.shared_kernel.enums import RoleEnum


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: uuid.UUID
    phone: str
    role: RoleEnum
