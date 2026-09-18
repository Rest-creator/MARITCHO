import uuid
from dataclasses import dataclass
from datetime import datetime

# Today: just the one provider. Kept as a plain constant (not an enum) since
# it's a payments-app-internal identifier, not a cross-app value type.
ECOCASH_PROVIDER = "ECOCASH"


@dataclass
class PaymentGatewayConfig:
    """Admin-editable credentials for a payment gateway (ADR-002).

    `api_key` is stored as plain text today. That is a known, documented
    limitation, not an oversight: production hardening (encryption at
    rest, or a real secrets manager) is out of scope for this pass and
    should happen before real credentials are ever entered.
    """

    provider: str
    merchant_code: str | None = None
    api_key: str | None = None
    base_url: str | None = None
    is_sandbox: bool = True
    updated_at: datetime | None = None


@dataclass
class EcoCashCallbackLog:
    """Append-only, unauthenticated-shape log of every EcoCash webhook call
    received. Deliberately not reconciled back into ledger tables by
    mutation (those rows are immutable) — this is a raw audit trail only.
    """

    id: uuid.UUID
    external_reference: str
    raw_payload: str
    received_at: datetime | None = None
