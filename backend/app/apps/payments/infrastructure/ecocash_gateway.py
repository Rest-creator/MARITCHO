"""EcoCash merchant-collection client (ADR-002).

Honesty note, read before touching this file: no real EcoCash API
documentation or sandbox credentials were available when this was
written. The request/response shape below is a best-effort guess at a
typical mobile-money merchant "collection request" API, not a verified
integration. Treat this as a real, working client against *a* plausible
shape, wired up correctly end-to-end (config, auth header, error
handling), but re-check every field name and endpoint path against
EcoCash's actual documentation before this ever runs against production
traffic. Likewise, `verify_webhook_auth` is a coarse, unverified stand-in
for real webhook signature verification — EcoCash's actual callback-
authentication scheme is unknown.
"""

from decimal import Decimal

import httpx

from app.apps.payments.domain.entities import ECOCASH_PROVIDER
from app.apps.payments.domain.repositories import PaymentGatewayConfigRepository
from app.shared_kernel.exceptions import (
    PaymentGatewayNotConfiguredError,
    PaymentGatewayRequestError,
)
from app.shared_kernel.ports import PaymentCollectionPort

_REQUEST_TIMEOUT_SECONDS = 15.0


class EcoCashGateway(PaymentCollectionPort):
    def __init__(self, configs: PaymentGatewayConfigRepository) -> None:
        self._configs = configs

    async def initiate_collection(self, *, phone: str, amount: Decimal, reference: str) -> str:
        """Raises PaymentGatewayNotConfiguredError / PaymentGatewayRequestError
        (both auto-translated to 503/502 by the global exception handlers —
        no try/except needed at the call site)."""
        config = await self._configs.get(ECOCASH_PROVIDER)
        if (
            config is None
            or not config.merchant_code
            or not config.api_key
            or not config.base_url
        ):
            raise PaymentGatewayNotConfiguredError(
                "EcoCash is not configured — set merchant_code, api_key, and base_url "
                "via PUT /admin/payment-gateways/ecocash first"
            )

        payload = {
            "merchantCode": config.merchant_code,
            "msisdn": phone,
            "amount": str(amount),
            "currency": "USD",
            "reference": reference,
        }
        headers = {"Authorization": f"Bearer {config.api_key}"}

        try:
            async with httpx.AsyncClient(timeout=_REQUEST_TIMEOUT_SECONDS) as client:
                response = await client.post(
                    f"{config.base_url}/collections", json=payload, headers=headers
                )
            response.raise_for_status()
            body = response.json()
        except httpx.HTTPError as exc:
            raise PaymentGatewayRequestError(f"EcoCash collection request failed: {exc}") from exc

        external_reference = body.get("transactionReference")
        if not external_reference:
            raise PaymentGatewayRequestError(
                "EcoCash collection response did not include a transactionReference"
            )
        return str(external_reference)

    async def verify_webhook_auth(self, authorization_header: str | None) -> bool:
        config = await self._configs.get(ECOCASH_PROVIDER)
        if config is None or not config.api_key:
            return False
        return authorization_header == f"Bearer {config.api_key}"
