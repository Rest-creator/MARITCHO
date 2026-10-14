import uuid
from dataclasses import dataclass
from datetime import datetime

from app.shared_kernel.enums import RoleEnum


@dataclass
class Person:
    id: uuid.UUID
    phone: str
    role: RoleEnum
    next_of_kin_phone: str | None = None
    guarantor_id: uuid.UUID | None = None
    created_at: datetime | None = None
    display_name: str | None = None
    is_available: bool = True
    travel_km: int = 50
    home_suburb: str | None = None
