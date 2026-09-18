import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.shared_kernel.enums import RoleEnum


class PersonModel(Base):
    __tablename__ = "persons"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phone: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    role: Mapped[RoleEnum] = mapped_column(Enum(RoleEnum), nullable=False)
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
