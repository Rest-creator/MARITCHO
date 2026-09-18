from app.apps.payments.infrastructure.ecocash_gateway import EcoCashGateway
from app.apps.payments.infrastructure.models import (
    PaymentGatewayConfigModel as PaymentGatewayConfig,
)
from app.shared_kernel.enums import TradeEnum
from tests.conftest import auth_headers

JOB_PAYLOAD = {
    "trade": "PLUMBING",
    "suburb": "Nkulumane",
    "address": "12 Fife Street, Nkulumane",
    "problem_description": "Leaking geyser in the bathroom, water on the floor.",
}

ORDER_PAYLOAD = {
    "trade": "BUILDING",
    "suburb": "Nkulumane",
    "address": "Site 7, Nkulumane Industrial Area",
    "workers_needed": 2,
    "problem_description": "Need bricklayers for a 2-day wall job.",
}


async def _create_matched_job(client, buyer, worker_factory):
    worker = await worker_factory(TradeEnum.PLUMBING, "Nkulumane")
    create_response = await client.post(
        "/jobs/request", json=JOB_PAYLOAD, headers=auth_headers(buyer)
    )
    job = create_response.json()
    await client.get(f"/jobs/{job['id']}/matches", headers=auth_headers(buyer))
    return job, worker


async def _clear_config(db_session):
    existing = await db_session.get(PaymentGatewayConfig, "ECOCASH")
    if existing is not None:
        await db_session.delete(existing)
        await db_session.commit()


async def test_book_with_usd_currency_defaults_and_skips_ecocash(
    client, buyer, worker_factory, monkeypatch
):
    """The default (no currency in payload) must behave exactly as before —
    no EcoCash call attempted at all."""
    job, worker = await _create_matched_job(client, buyer, worker_factory)

    async def _fail_if_called(self, *args, **kwargs):
        raise AssertionError("initiate_collection should not be called for USD bookings")

    monkeypatch.setattr(EcoCashGateway, "initiate_collection", _fail_if_called)

    response = await client.post(
        f"/jobs/{job['id']}/book",
        json={"worker_id": str(worker.id), "deposit_amount": "50.00"},
        headers=auth_headers(buyer),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["currency"] == "USD"


async def test_book_with_ecocash_currency_fails_when_not_configured(
    client, buyer, worker_factory, db_session
):
    await _clear_config(db_session)
    job, worker = await _create_matched_job(client, buyer, worker_factory)

    response = await client.post(
        f"/jobs/{job['id']}/book",
        json={
            "worker_id": str(worker.id),
            "deposit_amount": "50.00",
            "currency": "ECOCASH",
        },
        headers=auth_headers(buyer),
    )

    assert response.status_code == 503


async def test_book_with_ecocash_currency_succeeds_when_configured(
    client, buyer, worker_factory, monkeypatch
):
    job, worker = await _create_matched_job(client, buyer, worker_factory)

    async def _fake_initiate_collection(self, *, phone, amount, reference):
        assert reference == job["id"]
        return "ECOCASH-REF-XYZ"

    monkeypatch.setattr(EcoCashGateway, "initiate_collection", _fake_initiate_collection)

    response = await client.post(
        f"/jobs/{job['id']}/book",
        json={
            "worker_id": str(worker.id),
            "deposit_amount": "50.00",
            "currency": "ECOCASH",
        },
        headers=auth_headers(buyer),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["currency"] == "ECOCASH"

    ledger_response = await client.get(f"/jobs/{job['id']}/ledger", headers=auth_headers(buyer))
    entries = ledger_response.json()
    assert len(entries) == 1
    assert entries[0]["currency"] == "ECOCASH"
    assert entries[0]["external_reference"] == "ECOCASH-REF-XYZ"


async def test_book_crew_order_with_ecocash_currency_succeeds_when_configured(
    client, buyer, aggregator, worker_factory, monkeypatch
):
    await client.post(
        "/crews/me", json={"name": "Baba Moyo Crew"}, headers=auth_headers(aggregator)
    )
    for _ in range(2):
        w = await worker_factory(TradeEnum.BUILDING, "Nkulumane")
        await client.post(
            "/crews/me/members", json={"worker_id": str(w.id)}, headers=auth_headers(aggregator)
        )
    crew = (await client.get("/crews/me", headers=auth_headers(aggregator))).json()

    order_response = await client.post(
        "/crew-orders/request", json=ORDER_PAYLOAD, headers=auth_headers(buyer)
    )
    order = order_response.json()
    await client.get(f"/crew-orders/{order['id']}/matches", headers=auth_headers(buyer))

    async def _fake_initiate_collection(self, *, phone, amount, reference):
        assert reference == order["id"]
        return "ECOCASH-REF-CREW"

    monkeypatch.setattr(EcoCashGateway, "initiate_collection", _fake_initiate_collection)

    response = await client.post(
        f"/crew-orders/{order['id']}/book",
        json={"crew_id": crew["id"], "deposit_amount": "500.00", "currency": "ECOCASH"},
        headers=auth_headers(buyer),
    )

    assert response.status_code == 200
    assert response.json()["currency"] == "ECOCASH"

    ledger_response = await client.get(
        f"/crew-orders/{order['id']}/ledger", headers=auth_headers(buyer)
    )
    entries = ledger_response.json()
    assert entries[0]["currency"] == "ECOCASH"
    assert entries[0]["external_reference"] == "ECOCASH-REF-CREW"
