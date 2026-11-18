"""Messaging timestamps, history paging and unread notifications."""

from datetime import datetime

from tests.conftest import auth_headers
from tests.test_messaging import _create_booked_job


async def _send(client, job_id: str, sender, body: str) -> dict[str, object]:
    response = await client.post(
        f"/jobs/{job_id}/messages",
        json={"message_type": "TEXT", "body": body},
        headers=auth_headers(sender),
    )
    assert response.status_code == 201, response.text
    return dict(response.json())


async def test_sent_message_time_carries_a_utc_offset(client, buyer, worker_factory):
    job, _ = await _create_booked_job(client, buyer, worker_factory)
    sent = await _send(client, job["id"], buyer, "On my way")

    # Without an offset, browsers read UTC as local time (2 hours early in CAT).
    created = datetime.fromisoformat(str(sent["created_at"]).replace("Z", "+00:00"))
    offset = created.utcoffset()
    assert offset is not None
    assert offset.total_seconds() == 0


async def test_history_returns_the_newest_page_oldest_first(client, buyer, worker_factory):
    job, worker = await _create_booked_job(client, buyer, worker_factory)
    for index in range(5):
        await _send(client, job["id"], buyer, f"message {index}")

    page = await client.get(
        f"/jobs/{job['id']}/messages", params={"limit": 3}, headers=auth_headers(worker)
    )
    assert page.status_code == 200
    # The latest three, in reading order — not the first three ever sent.
    assert [message["body"] for message in page.json()] == ["message 2", "message 3", "message 4"]


async def test_unread_summary_counts_new_messages_until_read(client, buyer, worker_factory):
    job, worker = await _create_booked_job(client, buyer, worker_factory)
    await _send(client, job["id"], buyer, "Hello, can you come today?")
    await _send(client, job["id"], buyer, "The geyser is still leaking")

    summary = await client.get("/messages/unread", headers=auth_headers(worker))
    assert summary.status_code == 200
    [conversation] = summary.json()
    assert conversation["job_id"] == job["id"]
    assert conversation["unread_count"] == 2
    assert conversation["last_message_preview"] == "The geyser is still leaking"
    assert conversation["last_sender_id"] == str(buyer.id)

    # The sender has nothing unread in their own conversation.
    [own] = (await client.get("/messages/unread", headers=auth_headers(buyer))).json()
    assert own["unread_count"] == 0

    read = await client.post(f"/jobs/{job['id']}/messages/read", headers=auth_headers(worker))
    assert read.status_code == 204
    [after] = (await client.get("/messages/unread", headers=auth_headers(worker))).json()
    assert after["unread_count"] == 0


async def test_unread_summary_excludes_strangers(client, buyer, other_buyer, worker_factory):
    job, _ = await _create_booked_job(client, buyer, worker_factory)
    await _send(client, job["id"], buyer, "Private")

    response = await client.get("/messages/unread", headers=auth_headers(other_buyer))
    assert response.status_code == 200
    assert response.json() == []
