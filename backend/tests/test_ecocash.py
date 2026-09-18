import json
from decimal import Decimal

import httpx
import pytest

from app.apps.payments.infrastructure.ecocash_gateway import EcoCashGateway
from app.apps.payments.infrastructure.models import (
    PaymentGatewayConfigModel as PaymentGatewayConfig,
)
from app.apps.payments.infrastructure.repositories import SqlAlchemyPaymentGatewayConfigRepository
from app.shared_kernel.exceptions import (
    PaymentGatewayNotConfiguredError,
    PaymentGatewayRequestError,
)


def _gateway(db_session) -> EcoCashGateway:
    return EcoCashGateway(SqlAlchemyPaymentGatewayConfigRepository(db_session))


async def _configure(db_session, *, api_key="test-api-key"):
    config = await db_session.get(PaymentGatewayConfig, "ECOCASH")
    if config is None:
        config = PaymentGatewayConfig(provider="ECOCASH")
        db_session.add(config)
    config.merchant_code = "MERCH123"
    config.api_key = api_key
    config.base_url = "https://ecocash.example.test"
    config.is_sandbox = True
    await db_session.commit()
    await db_session.refresh(config)
    return config


_RealAsyncClient = httpx.AsyncClient


def _patch_transport(monkeypatch, handler):
    def _client_factory(*args, **kwargs):
        kwargs.pop("timeout", None)
        return _RealAsyncClient(transport=httpx.MockTransport(handler), **kwargs)

    monkeypatch.setattr(
        "app.apps.payments.infrastructure.ecocash_gateway.httpx.AsyncClient", _client_factory
    )


async def test_initiate_collection_raises_when_not_configured(db_session):
    existing = await db_session.get(PaymentGatewayConfig, "ECOCASH")
    if existing is not None:
        await db_session.delete(existing)
        await db_session.commit()

    with pytest.raises(PaymentGatewayNotConfiguredError):
        await _gateway(db_session).initiate_collection(
            phone="+263771234567", amount=Decimal("10.00"), reference="job-1"
        )


async def test_initiate_collection_returns_reference_on_success(db_session, monkeypatch):
    await _configure(db_session)

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        assert body["merchantCode"] == "MERCH123"
        assert body["msisdn"] == "+263771234567"
        assert body["amount"] == "10.00"
        assert body["reference"] == "job-1"
        assert request.headers["authorization"] == "Bearer test-api-key"
        return httpx.Response(200, json={"transactionReference": "ECOCASH-REF-1"})

    _patch_transport(monkeypatch, handler)

    reference = await _gateway(db_session).initiate_collection(
        phone="+263771234567", amount=Decimal("10.00"), reference="job-1"
    )

    assert reference == "ECOCASH-REF-1"


async def test_initiate_collection_raises_on_error_status(db_session, monkeypatch):
    await _configure(db_session)

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={"error": "internal"})

    _patch_transport(monkeypatch, handler)

    with pytest.raises(PaymentGatewayRequestError):
        await _gateway(db_session).initiate_collection(
            phone="+263771234567", amount=Decimal("10.00"), reference="job-1"
        )


async def test_initiate_collection_raises_when_reference_missing(db_session, monkeypatch):
    await _configure(db_session)

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"status": "accepted"})

    _patch_transport(monkeypatch, handler)

    with pytest.raises(PaymentGatewayRequestError):
        await _gateway(db_session).initiate_collection(
            phone="+263771234567", amount=Decimal("10.00"), reference="job-1"
        )


async def test_verify_webhook_auth_matches_configured_key(db_session):
    await _configure(db_session)
    gateway = _gateway(db_session)

    assert await gateway.verify_webhook_auth("Bearer test-api-key") is True
    assert await gateway.verify_webhook_auth("Bearer wrong-key") is False
    assert await gateway.verify_webhook_auth(None) is False


async def test_verify_webhook_auth_rejects_when_not_configured(db_session):
    existing = await db_session.get(PaymentGatewayConfig, "ECOCASH")
    if existing is not None:
        await db_session.delete(existing)
        await db_session.commit()

    assert await _gateway(db_session).verify_webhook_auth("Bearer anything") is False
