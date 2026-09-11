from app.models import TradeEnum
from tests.conftest import auth_headers

JOB_PAYLOAD = {
    "trade": "PLUMBING",
    "suburb": "Nkulumane",
    "address": "12 Fife Street, Nkulumane",
    "problem_description": "Leaking geyser in the bathroom, water on the floor.",
}


async def _create_in_progress_job(client, buyer, worker_factory, deposit="50.00", quote="200.00"):
    worker = await worker_factory(TradeEnum.PLUMBING, "Nkulumane")

    create_response = await client.post(
        "/jobs/request", json=JOB_PAYLOAD, headers=auth_headers(buyer)
    )
    job = create_response.json()

    await client.get(f"/jobs/{job['id']}/matches", headers=auth_headers(buyer))
    await client.post(
        f"/jobs/{job['id']}/book",
        json={"worker_id": str(worker.id), "deposit_amount": deposit},
        headers=auth_headers(buyer),
    )
    await client.post(
        f"/jobs/{job['id']}/quote",
        json={"quote_amount": quote},
        headers=auth_headers(worker),
    )
    return job, worker


async def test_buyer_can_raise_dispute_and_it_freezes_the_job(client, buyer, worker_factory):
    job, worker = await _create_in_progress_job(client, buyer, worker_factory)

    response = await client.post(
        f"/jobs/{job['id']}/dispute",
        json={"reason": "The pipe is still leaking after the repair."},
        headers=auth_headers(buyer),
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "OPEN"
    assert body["worker_response"] is None

    job_response = await client.get(f"/jobs/{job['id']}", headers=auth_headers(buyer))
    assert job_response.json()["status"] == "DISPUTED"

    # No ledger entry was added by raising the dispute (money is frozen, not moved).
    ledger_response = await client.get(f"/jobs/{job['id']}/ledger", headers=auth_headers(buyer))
    entry_types = {e["entry_type"] for e in ledger_response.json()}
    assert entry_types == {"DEPOSIT_HELD", "BALANCE_COMMITTED"}


async def test_disputed_worker_standing_is_frozen(client, buyer, worker_factory):
    job, worker = await _create_in_progress_job(client, buyer, worker_factory)
    await client.post(
        f"/jobs/{job['id']}/dispute",
        json={"reason": "Not happy with the work."},
        headers=auth_headers(buyer),
    )

    response = await client.get("/workers/me/standing", headers=auth_headers(worker))

    assert response.status_code == 200
    assert response.json()["is_frozen"] is True


async def test_disputed_worker_excluded_from_new_matches(client, buyer, worker_factory):
    job, worker = await _create_in_progress_job(client, buyer, worker_factory)
    await client.post(
        f"/jobs/{job['id']}/dispute",
        json={"reason": "Not happy with the work."},
        headers=auth_headers(buyer),
    )

    other_job_response = await client.post(
        "/jobs/request", json=JOB_PAYLOAD, headers=auth_headers(buyer)
    )
    other_job = other_job_response.json()

    matches_response = await client.get(
        f"/jobs/{other_job['id']}/matches", headers=auth_headers(buyer)
    )

    assert matches_response.status_code == 200
    assert matches_response.json() == []


async def test_dispute_requires_in_progress_status(client, buyer, worker_factory):
    await worker_factory(TradeEnum.PLUMBING, "Nkulumane")
    create_response = await client.post(
        "/jobs/request", json=JOB_PAYLOAD, headers=auth_headers(buyer)
    )
    job = create_response.json()  # still REQUESTED

    response = await client.post(
        f"/jobs/{job['id']}/dispute",
        json={"reason": "Too early to dispute."},
        headers=auth_headers(buyer),
    )

    assert response.status_code == 409


async def test_dispute_rejects_non_owner_buyer(client, buyer, other_buyer, worker_factory):
    job, _worker = await _create_in_progress_job(client, buyer, worker_factory)

    response = await client.post(
        f"/jobs/{job['id']}/dispute",
        json={"reason": "Not my job but I'll try."},
        headers=auth_headers(other_buyer),
    )

    assert response.status_code == 403


async def test_worker_can_respond_and_dispute_resolves_to_return_visit(
    client, buyer, worker_factory
):
    job, worker = await _create_in_progress_job(client, buyer, worker_factory)
    await client.post(
        f"/jobs/{job['id']}/dispute",
        json={"reason": "The pipe is still leaking."},
        headers=auth_headers(buyer),
    )

    response = await client.post(
        f"/jobs/{job['id']}/dispute/respond",
        json={
            "response": "I'll come back tomorrow morning to fix the seal properly.",
            "before_photo_url": "https://example.com/before.jpg",
            "after_photo_url": "https://example.com/after.jpg",
        },
        headers=auth_headers(worker),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "RESOLVED_RETURN_VISIT"
    assert "come back tomorrow" in body["worker_response"]
    assert body["after_photo_url"] == "https://example.com/after.jpg"

    job_response = await client.get(f"/jobs/{job['id']}", headers=auth_headers(buyer))
    assert job_response.json()["status"] == "IN_PROGRESS"

    standing_response = await client.get("/workers/me/standing", headers=auth_headers(worker))
    assert standing_response.json()["is_frozen"] is False


async def test_after_return_visit_job_can_be_completed_normally(client, buyer, worker_factory):
    job, worker = await _create_in_progress_job(client, buyer, worker_factory)
    await client.post(
        f"/jobs/{job['id']}/dispute",
        json={"reason": "The pipe is still leaking."},
        headers=auth_headers(buyer),
    )
    await client.post(
        f"/jobs/{job['id']}/dispute/respond",
        json={"response": "Fixed the seal properly this time."},
        headers=auth_headers(worker),
    )

    response = await client.post(
        f"/jobs/{job['id']}/complete",
        json={"what_was_done": "Refitted the pipe seal after a return visit."},
        headers=auth_headers(buyer),
    )

    assert response.status_code == 200
    assert response.json()["status"] == "COMPLETED"


async def test_respond_rejects_non_assigned_worker(client, buyer, worker_factory):
    job, _worker = await _create_in_progress_job(client, buyer, worker_factory)
    await client.post(
        f"/jobs/{job['id']}/dispute",
        json={"reason": "Not happy."},
        headers=auth_headers(buyer),
    )
    impostor = await worker_factory(TradeEnum.PLUMBING, "Njube")

    response = await client.post(
        f"/jobs/{job['id']}/dispute/respond",
        json={"response": "I'll fix it."},
        headers=auth_headers(impostor),
    )

    assert response.status_code == 403


async def test_respond_requires_disputed_status(client, buyer, worker_factory):
    job, worker = await _create_in_progress_job(client, buyer, worker_factory)
    # never disputed, still IN_PROGRESS

    response = await client.post(
        f"/jobs/{job['id']}/dispute/respond",
        json={"response": "Nothing to respond to."},
        headers=auth_headers(worker),
    )

    assert response.status_code == 409


async def test_list_disputes_visible_to_party_not_others(
    client, buyer, other_buyer, worker_factory
):
    job, _worker = await _create_in_progress_job(client, buyer, worker_factory)
    await client.post(
        f"/jobs/{job['id']}/dispute",
        json={"reason": "Not happy."},
        headers=auth_headers(buyer),
    )

    own_response = await client.get(
        f"/jobs/{job['id']}/disputes", headers=auth_headers(buyer)
    )
    assert own_response.status_code == 200
    assert len(own_response.json()) == 1

    foreign_response = await client.get(
        f"/jobs/{job['id']}/disputes", headers=auth_headers(other_buyer)
    )
    assert foreign_response.status_code == 403
