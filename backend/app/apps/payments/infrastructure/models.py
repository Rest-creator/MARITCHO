import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class PaymentGatewayConfigModel(Base):
    __tablename__ = "payment_gateway_configs"
    provider: Mapped[str] = mapped_column(String(20), primary_key=True)
    merchant_code: Mapped[str | None] = mapped_column(String(100))
    api_key: Mapped[str | None] = mapped_column(String(255))
    base_url: Mapped[str | None] = mapped_column(String(255))
    is_sandbox: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )


class EcoCashCallbackLogModel(Base):
    __tablename__ = "ecocash_callback_logs"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    external_reference: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    raw_payload: Mapped[str] = mapped_column(Text, nullable=False)
    received_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
