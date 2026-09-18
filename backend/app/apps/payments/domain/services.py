from app.apps.payments.domain.entities import PaymentGatewayConfig
from app.apps.payments.domain.repositories import (
    EcoCashCallbackLogRepository,
    PaymentGatewayConfigRepository,
)
from app.core.exceptions import NotFoundError
from app.shared_kernel.unit_of_work import UnitOfWork


class GetGatewayConfigUseCase:
    def __init__(self, configs: PaymentGatewayConfigRepository) -> None:
        self._configs = configs

    async def execute(self, provider: str) -> PaymentGatewayConfig:
        config = await self._configs.get(provider)
        if config is None:
            raise NotFoundError(f"{provider} is not configured yet")
        return config


class SetGatewayConfigUseCase:
    """Set (or replace) a gateway's merchant credentials, OPS-only.

    Entered from the admin side at runtime, not via env vars, per the
    product decision behind ADR-002 — credentials can be added/rotated
    without a redeploy.
    """

    def __init__(self, configs: PaymentGatewayConfigRepository, uow: UnitOfWork) -> None:
        self._configs = configs
        self._uow = uow

    async def execute(
        self,
        *,
        provider: str,
        merchant_code: str | None,
        api_key: str | None,
        base_url: str | None,
        is_sandbox: bool,
    ) -> PaymentGatewayConfig:
        config = await self._configs.upsert(
            provider=provider,
            merchant_code=merchant_code,
            api_key=api_key,
            base_url=base_url,
            is_sandbox=is_sandbox,
        )
        await self._uow.commit()
        return config


class RecordWebhookCallbackUseCase:
    """Logs a raw webhook payload as an append-only audit record.

    Auth verification happens in the router before this is called (see
    EcoCashGateway.verify_webhook_auth) — this use case only records.
    """

    def __init__(self, logs: EcoCashCallbackLogRepository, uow: UnitOfWork) -> None:
        self._logs = logs
        self._uow = uow

    async def execute(self, *, reference: str, raw_payload: str) -> None:
        await self._logs.add(external_reference=reference, raw_payload=raw_payload)
        await self._uow.commit()
