from sqlalchemy.ext.asyncio import AsyncSession

from app.apps.payments.domain.entities import EcoCashCallbackLog, PaymentGatewayConfig
from app.apps.payments.domain.repositories import (
    EcoCashCallbackLogRepository,
    PaymentGatewayConfigRepository,
)
from app.apps.payments.infrastructure.models import (
    EcoCashCallbackLogModel,
    PaymentGatewayConfigModel,
)


def _config_to_entity(model: PaymentGatewayConfigModel) -> PaymentGatewayConfig:
    return PaymentGatewayConfig(
        provider=model.provider,
        merchant_code=model.merchant_code,
        api_key=model.api_key,
        base_url=model.base_url,
        is_sandbox=model.is_sandbox,
        updated_at=model.updated_at,
    )


def _log_to_entity(model: EcoCashCallbackLogModel) -> EcoCashCallbackLog:
    return EcoCashCallbackLog(
        id=model.id,
        external_reference=model.external_reference,
        raw_payload=model.raw_payload,
        received_at=model.received_at,
    )


class SqlAlchemyPaymentGatewayConfigRepository(PaymentGatewayConfigRepository):
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get(self, provider: str) -> PaymentGatewayConfig | None:
        model = await self._db.get(PaymentGatewayConfigModel, provider)
        return _config_to_entity(model) if model else None

    async def upsert(
        self,
        *,
        provider: str,
        merchant_code: str | None,
        api_key: str | None,
        base_url: str | None,
        is_sandbox: bool,
    ) -> PaymentGatewayConfig:
        model = await self._db.get(PaymentGatewayConfigModel, provider)
        if model is None:
            model = PaymentGatewayConfigModel(provider=provider)
            self._db.add(model)
        model.merchant_code = merchant_code
        model.api_key = api_key
        model.base_url = base_url
        model.is_sandbox = is_sandbox
        await self._db.flush()
        return _config_to_entity(model)


class SqlAlchemyEcoCashCallbackLogRepository(EcoCashCallbackLogRepository):
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def add(self, *, external_reference: str, raw_payload: str) -> EcoCashCallbackLog:
        model = EcoCashCallbackLogModel(
            external_reference=external_reference, raw_payload=raw_payload
        )
        self._db.add(model)
        await self._db.flush()
        return _log_to_entity(model)
