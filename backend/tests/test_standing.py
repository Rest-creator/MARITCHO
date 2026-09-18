from decimal import Decimal

from app.shared_kernel.enums import TradeEnum
from tests.conftest import auth_headers

JOB_PAYLOAD = {
    "trade": "PLUMBING",
    "suburb": "Nkulumane",
    "address": "12 Fife Street, Nkulumane",
    "problem_description": "Leaking geyser in the bathroom, water on the floor.",
}


async def _book_and_quote(client, buyer, worker, deposit="50.00", quote="200.00"):
    """Create a fresh job and take it through booking + quoting for `worker`."""
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
        json={"labor_amount": quote, "materials_amount": "0.00"},
        headers=auth_headers(worker),
    )
    return job


async def _get_standing(client, worker):
    response = await client.get("/workers/me/standing", headers=auth_headers(worker))
    assert response.status_code == 200
    return response.json()


async def test_completing_a_job_updates_standing(client, buyer, worker_factory):
    worker = await worker_factory(TradeEnum.PLUMBING, "Nkulumane")
    job = await _book_and_quote(client, buyer, worker)

    response = await client.post(
        f"/jobs/{job['id']}/complete",
        json={"what_was_done": "Replaced the geyser element."},
        headers=auth_headers(buyer),
    )
    assert response.status_code == 200

    standing = await _get_standing(client, worker)
    assert standing["jobs_completed"] == 1
    assert Decimal(standing["fill_rate"]) == Decimal("100.00")
    assert Decimal(standing["dispute_rate"]) == Decimal("0.00")
    assert Decimal(standing["on_time_rate"]) == Decimal("100.00")


async def test_raising_a_dispute_updates_dispute_rate_immediately(
    client, buyer, worker_factory
):
    worker = await worker_factory(TradeEnum.PLUMBING, "Nkulumane")
    job = await _book_and_quote(client, buyer, worker)

    response = await client.post(
        f"/jobs/{job['id']}/dispute",
        json={"reason": "Still leaking."},
        headers=auth_headers(buyer),
    )
    assert response.status_code == 201

    standing = await _get_standing(client, worker)
    assert standing["jobs_completed"] == 0
    assert Decimal(standing["dispute_rate"]) == Decimal("100.00")


async def test_disputed_then_completed_job_lowers_on_time_rate_not_fill_rate(
    client, buyer, worker_factory
):
    worker = await worker_factory(TradeEnum.PLUMBING, "Nkulumane")
    job = await _book_and_quote(client, buyer, worker)

    await client.post(
        f"/jobs/{job['id']}/dispute",
        json={"reason": "Still leaking."},
        headers=auth_headers(buyer),
    )
    await client.post(
        f"/jobs/{job['id']}/dispute/respond",
        json={"response": "Fixed it properly this time."},
        headers=auth_headers(worker),
    )
    response = await client.post(
        f"/jobs/{job['id']}/complete",
        json={"what_was_done": "Refitted the seal after a return visit."},
        headers=auth_headers(buyer),
    )
    assert response.status_code == 200

    standing = await _get_standing(client, worker)
    assert standing["jobs_completed"] == 1
    # Completed, so fill_rate is full — but it was disputed, so on_time_rate is not.
    assert Decimal(standing["fill_rate"]) == Decimal("100.00")
    assert Decimal(standing["dispute_rate"]) == Decimal("100.00")
    assert Decimal(standing["on_time_rate"]) == Decimal("0.00")


async def test_standing_averages_across_multiple_jobs_for_the_same_worker(
    client, buyer, worker_factory
):
    worker = await worker_factory(TradeEnum.PLUMBING, "Nkulumane")

    # Job 1: completed cleanly.
    clean_job = await _book_and_quote(client, buyer, worker)
    await client.post(
        f"/jobs/{clean_job['id']}/complete",
        json={"what_was_done": "Done cleanly."},
        headers=auth_headers(buyer),
    )

    # Job 2: disputed, then completed after a return visit.
    disputed_job = await _book_and_quote(client, buyer, worker)
    await client.post(
        f"/jobs/{disputed_job['id']}/dispute",
        json={"reason": "Not happy."},
        headers=auth_headers(buyer),
    )
    await client.post(
        f"/jobs/{disputed_job['id']}/dispute/respond",
        json={"response": "Fixed."},
        headers=auth_headers(worker),
    )
    await client.post(
        f"/jobs/{disputed_job['id']}/complete",
        json={"what_was_done": "Done after a return visit."},
        headers=auth_headers(buyer),
    )

    standing = await _get_standing(client, worker)
    assert standing["jobs_completed"] == 2
    assert Decimal(standing["fill_rate"]) == Decimal("100.00")
    assert Decimal(standing["dispute_rate"]) == Decimal("50.00")
    assert Decimal(standing["on_time_rate"]) == Decimal("50.00")
