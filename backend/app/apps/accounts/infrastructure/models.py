import uuid
from datetime import datetime

from sqlalchemy import Boolean, ColumnElement, DateTime, Enum, ForeignKey, Integer, String, or_
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.shared_kernel.enums import RoleEnum


class PersonModel(Base):
    __tablename__ = "persons"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phone: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    # Active mode: drives navigation and which side shared screens act as.
    role: Mapped[RoleEnum] = mapped_column(Enum(RoleEnum), nullable=False)
    # Capabilities this account has unlocked (role values). One account can
    # hire and find work; switching modes never removes the other side.
    roles: Mapped[list[str]] = mapped_column(
        ARRAY(String(16)), nullable=False, default=list, server_default="{}"
    )
    # See docs/architecture/database_schema_design.md §2.8: this asymmetry
    # (guarantor_id is a proper FK, next_of_kin_phone is a bare string) is
    # intentional — a guarantor is expected to be a registered person, a
    # next of kin is expected to often not be. Both columns are currently
    # dormant (no endpoint reads/writes either).
    next_of_kin_phone: Mapped[str | None] = mapped_column(String(20))
    guarantor_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("persons.id"), index=True
    )
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
    display_name: Mapped[str | None] = mapped_column(String(100))
    is_available: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    travel_km: Mapped[int] = mapped_column(Integer, nullable=False, default=50)
    home_suburb: Mapped[str | None] = mapped_column(String(100), ForeignKey("suburbs.name"))
    password_hash: Mapped[str | None] = mapped_column(String(255))


def person_can_act_as(role: RoleEnum) -> ColumnElement[bool]:
    """SQL filter: the person has `role` as a capability (any active mode)."""
    return or_(PersonModel.role == role, PersonModel.roles.any(role.value))


def model_can_act_as(model: PersonModel, role: RoleEnum) -> bool:
    return model.role == role or role.value in (model.roles or [])
