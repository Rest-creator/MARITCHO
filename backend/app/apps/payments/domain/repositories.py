from abc import ABC, abstractmethod

from app.apps.payments.domain.entities import EcoCashCallbackLog, PaymentGatewayConfig


class PaymentGatewayConfigRepository(ABC):
    @abstractmethod
    async def get(self, provider: str) -> PaymentGatewayConfig | None: ...

    @abstractmethod
    async def upsert(
        self,
        *,
        provider: str,
        merchant_code: str | None,
        api_key: str | None,
        base_url: str | None,
        is_sandbox: bool,
    ) -> PaymentGatewayConfig:
        """Stages the write (add/flush) but does not commit."""


class EcoCashCallbackLogRepository(ABC):
    @abstractmethod
    async def add(self, *, external_reference: str, raw_payload: str) -> EcoCashCallbackLog:
        """Stages the write (add/flush) but does not commit."""
