from app.shared_kernel.enums import TradeEnum
from tests.conftest import auth_headers

JOB_PAYLOAD = {
    "trade": "PLUMBING",
    "suburb": "Nkulumane",
    "address": "12 Fife Street, Nkulumane",
    "problem_description": "Leaking geyser in the bathroom, water on the floor.",
}


async def _create_booked_job(client, buyer, worker_factory):
    worker = await worker_factory(TradeEnum.PLUMBING, "Nkulumane")
    create_response = await client.post(
        "/jobs/request", json=JOB_PAYLOAD, headers=auth_headers(buyer)
    )
    job = create_response.json()
    await client.get(f"/jobs/{job['id']}/matches", headers=auth_headers(buyer))
    await client.post(
        f"/jobs/{job['id']}/book",
        json={"worker_id": str(worker.id), "deposit_amount": "50.00"},
        headers=auth_headers(buyer),
    )
    return job, worker


async def test_buyer_can_send_and_list_messages(client, buyer, worker_factory):
    job, worker = await _create_booked_job(client, buyer, worker_factory)

    response = await client.post(
        f"/jobs/{job['id']}/messages",
        json={"message_type": "TEXT", "body": "I can come at 2pm"},
        headers=auth_headers(buyer),
    )
    assert response.status_code == 201
    body = response.json()
    assert body["body"] == "I can come at 2pm"
    assert body["message_type"] == "TEXT"
    assert body["read_at"] is None

    list_response = await client.get(
        f"/jobs/{job['id']}/messages", headers=auth_headers(worker)
    )
    assert list_response.status_code == 200
    messages = list_response.json()
    assert len(messages) == 1
    assert messages[0]["body"] == "I can come at 2pm"


async def test_non_party_cannot_send_or_list_messages(client, buyer, worker_factory, other_buyer):
    job, _worker = await _create_booked_job(client, buyer, worker_factory)

    send_response = await client.post(
        f"/jobs/{job['id']}/messages",
        json={"message_type": "TEXT", "body": "snooping"},
        headers=auth_headers(other_buyer),
    )
    assert send_response.status_code == 403

    list_response = await client.get(
        f"/jobs/{job['id']}/messages", headers=auth_headers(other_buyer)
    )
    assert list_response.status_code == 403


async def test_messages_on_missing_job_return_404(client, buyer):
    missing_id = "00000000-0000-0000-0000-000000000000"

    response = await client.post(
        f"/jobs/{missing_id}/messages",
        json={"message_type": "TEXT", "body": "hello"},
        headers=auth_headers(buyer),
    )

    assert response.status_code == 404


async def test_text_message_requires_a_body(client, buyer, worker_factory):
    job, _worker = await _create_booked_job(client, buyer, worker_factory)

    response = await client.post(
        f"/jobs/{job['id']}/messages",
        json={"message_type": "TEXT"},
        headers=auth_headers(buyer),
    )

    assert response.status_code == 422


async def test_voice_note_requires_media_url(client, buyer, worker_factory):
    job, _worker = await _create_booked_job(client, buyer, worker_factory)

    response = await client.post(
        f"/jobs/{job['id']}/messages",
        json={"message_type": "VOICE_NOTE", "duration_seconds": 18},
        headers=auth_headers(buyer),
    )

    assert response.status_code == 422


async def test_mark_messages_read_marks_the_other_partys_messages(
    client, buyer, worker_factory
):
    job, worker = await _create_booked_job(client, buyer, worker_factory)
    await client.post(
        f"/jobs/{job['id']}/messages",
        json={"message_type": "TEXT", "body": "hello"},
        headers=auth_headers(buyer),
    )

    read_response = await client.post(
        f"/jobs/{job['id']}/messages/read", headers=auth_headers(worker)
    )
    assert read_response.status_code == 204

    list_response = await client.get(
        f"/jobs/{job['id']}/messages", headers=auth_headers(buyer)
    )
    assert list_response.json()[0]["read_at"] is not None


# No automated test for the WebSocket route itself: httpx (this test
# module's client) has no WebSocket support at all, and the obvious
# alternative — Starlette's sync TestClient, which drives the ASGI app
# from its own thread via an anyio BlockingPortal — collides with this
# project's session-scoped async SQLAlchemy engine (its pooled asyncpg
# connections are bound to whichever event loop first touched them, and
# TestClient's portal thread runs on a different one; `engine.dispose()`
# before/after did not resolve it in practice — the failure recurred on
# the very first query even in isolation, suggesting a deeper SQLAlchemy
# async-via-greenlet / anyio-portal incompatibility, not a reuse bug).
#
# Verified instead with a genuine out-of-process smoke test: a real
# `uvicorn` server against the real Postgres/Redis containers, a plain
# `httpx.AsyncClient` for the REST calls, and the `websockets` library for
# the socket — confirming a message POSTed via `/jobs/{id}/messages`
# arrives in real time over an open `/jobs/{id}/ws` connection, and that a
# non-party's connection attempt is rejected (HTTP 403, since a
# pre-`accept()` close surfaces as a flat HTTP rejection under ASGI, not a
# WS close frame). See the dev-log entry in Backend_and_API/ named for
# this TestClient/SQLAlchemy incompatibility, and ADR-008 for the feature
# this belongs to.
