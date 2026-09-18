from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class EcoCashConfigUpdate(BaseModel):
    merchant_code: str | None = Field(default=None, max_length=100)
    api_key: str | None = Field(default=None, max_length=255)
    base_url: str | None = Field(default=None, max_length=255)
    is_sandbox: bool = True


class EcoCashConfigOut(BaseModel):
    provider: str
    merchant_code: str | None
    base_url: str | None
    is_sandbox: bool
    api_key_configured: bool
    updated_at: datetime | None


class EcoCashWebhookPayload(BaseModel):
    """Best-effort guess at EcoCash's callback shape — see
    ecocash_gateway.py's module docstring. All fields optional except
    `reference` so an unexpected real payload still gets logged rather
    than rejected."""

    reference: str
    status: str | None = None
    amount: Decimal | None = None
    msisdn: str | None = None
