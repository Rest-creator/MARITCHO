import json

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status

from app.apps.accounts.domain.entities import Person
from app.apps.accounts.interface_adapters.dependencies import RequireRole
from app.apps.payments.domain.entities import ECOCASH_PROVIDER, PaymentGatewayConfig
from app.apps.payments.domain.services import (
    GetGatewayConfigUseCase,
    RecordWebhookCallbackUseCase,
    SetGatewayConfigUseCase,
)
from app.apps.payments.infrastructure.ecocash_gateway import EcoCashGateway
from app.apps.payments.interface_adapters.dependencies import (
    get_ecocash_gateway,
    get_gateway_config_use_case,
    get_record_webhook_callback_use_case,
    get_set_gateway_config_use_case,
)
from app.apps.payments.interface_adapters.schemas import (
    EcoCashConfigOut,
    EcoCashConfigUpdate,
    EcoCashWebhookPayload,
)
from app.shared_kernel.enums import RoleEnum

router = APIRouter(tags=["payment-gateways"])


def _config_out(config: PaymentGatewayConfig) -> EcoCashConfigOut:
    return EcoCashConfigOut(
        provider=config.provider,
        merchant_code=config.merchant_code,
        base_url=config.base_url,
        is_sandbox=config.is_sandbox,
        api_key_configured=bool(config.api_key),
        updated_at=config.updated_at,
    )


@router.get("/admin/payment-gateways/ecocash", response_model=EcoCashConfigOut)
async def get_ecocash_config(
    current_user: Person = Depends(RequireRole([RoleEnum.OPS])),
    use_case: GetGatewayConfigUseCase = Depends(get_gateway_config_use_case),
) -> EcoCashConfigOut:
    config = await use_case.execute(ECOCASH_PROVIDER)
    return _config_out(config)


@router.put("/admin/payment-gateways/ecocash", response_model=EcoCashConfigOut)
async def set_ecocash_config(
    payload: EcoCashConfigUpdate,
    current_user: Person = Depends(RequireRole([RoleEnum.OPS])),
    use_case: SetGatewayConfigUseCase = Depends(get_set_gateway_config_use_case),
) -> EcoCashConfigOut:
    """Set (or replace) the EcoCash merchant credentials, OPS-only.

    Entered from the admin side at runtime, not via env vars, per the
    product decision behind ADR-002 — credentials can be added/rotated
    without a redeploy.
    """
    config = await use_case.execute(
        provider=ECOCASH_PROVIDER,
        merchant_code=payload.merchant_code,
        api_key=payload.api_key,
        base_url=payload.base_url,
        is_sandbox=payload.is_sandbox,
    )
    return _config_out(config)


@router.post("/webhooks/ecocash", status_code=status.HTTP_204_NO_CONTENT)
async def receive_ecocash_webhook(
    payload: EcoCashWebhookPayload,
    request: Request,
    authorization: str | None = Header(default=None),
    gateway: EcoCashGateway = Depends(get_ecocash_gateway),
    use_case: RecordWebhookCallbackUseCase = Depends(get_record_webhook_callback_use_case),
) -> None:
    """Receive an EcoCash payment-confirmation callback.

    Logged as a raw, append-only audit record (EcoCashCallbackLog) keyed
    by external_reference — deliberately not reconciled back into the
    immutable ledger tables. See ecocash_gateway.py's module docstring for
    what's genuinely verified here versus assumed.
    """
    if not await gateway.verify_webhook_auth(authorization):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid webhook auth")

    raw_body = await request.body()
    raw_payload = raw_body.decode("utf-8", errors="replace") or json.dumps(payload.model_dump())
    await use_case.execute(reference=payload.reference, raw_payload=raw_payload)
