import uuid
from dataclasses import dataclass, field
from datetime import datetime

from app.shared_kernel.enums import RoleEnum

# Roles a person can hold side by side and switch between themselves.
SELF_SERVICE_ROLES: frozenset[RoleEnum] = frozenset({RoleEnum.BUYER, RoleEnum.WORKER})


@dataclass
class Person:
    id: uuid.UUID
    phone: str
    # Active mode: navigation, home screen, and which side a shared screen
    # acts as (e.g. offer-stage job access is a worker-mode view).
    role: RoleEnum
    next_of_kin_phone: str | None = None
    guarantor_id: uuid.UUID | None = None
    created_at: datetime | None = None
    display_name: str | None = None
    is_available: bool = True
    travel_km: int = 50
    home_suburb: str | None = None
    password_hash: str | None = None
    # Capabilities unlocked on this account; always includes `role`.
    roles: frozenset[RoleEnum] = field(default_factory=frozenset)

    @property
    def capabilities(self) -> frozenset[RoleEnum]:
        return self.roles | {self.role}

    def acts_as(self, *roles: RoleEnum) -> bool:
        """True when the account may act in any of `roles`, whichever mode
        it is in right now (a recruiter who also finds work can be booked
        while browsing in hiring mode)."""
        return any(role in self.capabilities for role in roles)
