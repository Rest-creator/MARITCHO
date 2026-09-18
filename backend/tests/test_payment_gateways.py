from sqlalchemy import select

from app.apps.payments.infrastructure.models import (
    EcoCashCallbackLogModel as EcoCashCallbackLog,
)
from app.apps.payments.infrastructure.models import (
    PaymentGatewayConfigModel as PaymentGatewayConfig,
)
from tests.conftest import auth_headers


async def _clear_config(db_session):
    existing = await db_session.get(PaymentGatewayConfig, "ECOCASH")
    if existing is not None:
        await db_session.delete(existing)
        await db_session.commit()


async def test_ops_can_set_and_get_ecocash_config(client, ops_user, db_session):
    await _clear_config(db_session)

    set_response = await client.put(
        "/admin/payment-gateways/ecocash",
        json={
            "merchant_code": "MERCH123",
            "api_key": "super-secret-key",
            "base_url": "https://ecocash.example.test",
            "is_sandbox": True,
        },
        headers=auth_headers(ops_user),
    )

    assert set_response.status_code == 200
    body = set_response.json()
    assert body["merchant_code"] == "MERCH123"
    assert body["api_key_configured"] is True
    assert "api_key" not in body

    get_response = await client.get(
        "/admin/payment-gateways/ecocash", headers=auth_headers(ops_user)
    )
    assert get_response.status_code == 200
    assert get_response.json()["merchant_code"] == "MERCH123"


async def test_non_ops_cannot_set_config(client, buyer):
    response = await client.put(
        "/admin/payment-gateways/ecocash",
        json={"merchant_code": "X", "api_key": "Y", "base_url": "Z", "is_sandbox": True},
        headers=auth_headers(buyer),
    )

    assert response.status_code == 403


async def test_get_config_404_when_not_set(client, ops_user, db_session):
    await _clear_config(db_session)

    response = await client.get(
        "/admin/payment-gateways/ecocash", headers=auth_headers(ops_user)
    )

    assert response.status_code == 404


async def test_webhook_rejects_missing_or_wrong_auth(client, ops_user):
    await client.put(
        "/admin/payment-gateways/ecocash",
        json={
            "merchant_code": "MERCH123",
            "api_key": "webhook-key",
            "base_url": "https://ecocash.example.test",
            "is_sandbox": True,
        },
        headers=auth_headers(ops_user),
    )

    no_auth = await client.post(
        "/webhooks/ecocash", json={"reference": "job-1", "status": "confirmed"}
    )
    assert no_auth.status_code == 401

    wrong_auth = await client.post(
        "/webhooks/ecocash",
        json={"reference": "job-1", "status": "confirmed"},
        headers={"Authorization": "Bearer wrong-key"},
    )
    assert wrong_auth.status_code == 401


async def test_webhook_logs_payload_with_correct_auth(client, ops_user, db_session):
    await client.put(
        "/admin/payment-gateways/ecocash",
        json={
            "merchant_code": "MERCH123",
            "api_key": "webhook-key",
            "base_url": "https://ecocash.example.test",
            "is_sandbox": True,
        },
        headers=auth_headers(ops_user),
    )

    response = await client.post(
        "/webhooks/ecocash",
        json={"reference": "job-42", "status": "confirmed", "amount": "50.00"},
        headers={"Authorization": "Bearer webhook-key"},
    )

    assert response.status_code == 204

    result = await db_session.execute(
        select(EcoCashCallbackLog).where(EcoCashCallbackLog.external_reference == "job-42")
    )
    log = result.scalars().first()
    assert log is not None
    assert "job-42" in log.raw_payload
