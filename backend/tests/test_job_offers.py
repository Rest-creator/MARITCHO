from app.shared_kernel.enums import TradeEnum
from tests.conftest import auth_headers

JOB_PAYLOAD = {
    "trade": "PLUMBING",
    "suburb": "Nkulumane",
    "address": "12 Fife Street, Nkulumane",
    "problem_description": "Leaking geyser in the bathroom, water on the floor.",
}


async def _create_job(client, buyer, **overrides):
    payload = {**JOB_PAYLOAD, **overrides}
    response = await client.post("/jobs/request", json=payload, headers=auth_headers(buyer))
    assert response.status_code == 201
    return response.json()


async def test_worker_can_submit_an_offer_on_an_open_job(client, buyer, worker_factory):
    worker = await worker_factory(TradeEnum.PLUMBING, "Nkulumane")
    job = await _create_job(client, buyer)

    response = await client.post(
        f"/jobs/{job['id']}/offers",
        json={"quoted_amount": "35.00", "availability_note": "I can come at 2pm"},
        headers=auth_headers(worker),
    )

    assert response.status_code == 201
    body = response.json()
    assert body["quoted_amount"] == "35.00"
    assert body["availability_note"] == "I can come at 2pm"
    assert body["worker_id"] == str(worker.id)
    assert body["job_id"] == job["id"]


async def test_resubmitting_an_offer_revises_it(client, buyer, worker_factory):
    worker = await worker_factory(TradeEnum.PLUMBING, "Nkulumane")
    job = await _create_job(client, buyer)

    first = await client.post(
        f"/jobs/{job['id']}/offers",
        json={"quoted_amount": "35.00"},
        headers=auth_headers(worker),
    )
    second = await client.post(
        f"/jobs/{job['id']}/offers",
        json={"quoted_amount": "30.00", "availability_note": "Actually I can come now"},
        headers=auth_headers(worker),
    )

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["id"] == second.json()["id"]
    assert second.json()["quoted_amount"] == "30.00"
    assert second.json()["availability_note"] == "Actually I can come now"


async def test_offer_rejected_when_job_already_booked(client, buyer, worker_factory):
    worker = await worker_factory(TradeEnum.PLUMBING, "Nkulumane")
    other_worker = await worker_factory(TradeEnum.PLUMBING, "Nkulumane")
    job = await _create_job(client, buyer)
    await client.get(f"/jobs/{job['id']}/matches", headers=auth_headers(buyer))
    await client.post(
        f"/jobs/{job['id']}/book",
        json={"worker_id": str(worker.id), "deposit_amount": "50.00"},
        headers=auth_headers(buyer),
    )

    response = await client.post(
        f"/jobs/{job['id']}/offers",
        json={"quoted_amount": "35.00"},
        headers=auth_headers(other_worker),
    )

    assert response.status_code == 409


async def test_offer_rejected_when_worker_lacks_the_skill(client, buyer, worker_factory):
    worker = await worker_factory(TradeEnum.ELECTRICAL, "Nkulumane")
    job = await _create_job(client, buyer)

    response = await client.post(
        f"/jobs/{job['id']}/offers",
        json={"quoted_amount": "35.00"},
        headers=auth_headers(worker),
    )

    assert response.status_code == 422


async def test_offer_rejected_when_worker_already_busy(client, buyer, worker_factory):
    worker = await worker_factory(TradeEnum.PLUMBING, "Nkulumane")
    busy_job = await _create_job(client, buyer, problem_description="Another leak")
    await client.get(f"/jobs/{busy_job['id']}/matches", headers=auth_headers(buyer))
    await client.post(
        f"/jobs/{busy_job['id']}/book",
        json={"worker_id": str(worker.id), "deposit_amount": "50.00"},
        headers=auth_headers(buyer),
    )

    job = await _create_job(client, buyer)
    response = await client.post(
        f"/jobs/{job['id']}/offers",
        json={"quoted_amount": "35.00"},
        headers=auth_headers(worker),
    )

    assert response.status_code == 409


async def test_matches_surface_a_submitted_offer(client, buyer, worker_factory):
    worker = await worker_factory(TradeEnum.PLUMBING, "Nkulumane")
    job = await _create_job(client, buyer)
    await client.post(
        f"/jobs/{job['id']}/offers",
        json={"quoted_amount": "35.00", "availability_note": "I can come at 2pm"},
        headers=auth_headers(worker),
    )

    response = await client.get(f"/jobs/{job['id']}/matches", headers=auth_headers(buyer))

    assert response.status_code == 200
    candidates = response.json()
    assert len(candidates) == 1
    assert candidates[0]["worker_id"] == str(worker.id)
    assert candidates[0]["quoted_amount"] == "35.00"
    assert candidates[0]["availability_note"] == "I can come at 2pm"
    assert candidates[0]["quoted_at"] is not None


async def test_matches_include_offering_worker_beyond_three_suggestions(
    client, buyer, worker_factory
):
    best = await worker_factory(TradeEnum.PLUMBING, "Nkulumane")
    second = await worker_factory(TradeEnum.PLUMBING, "Nkulumane")
    third = await worker_factory(TradeEnum.PLUMBING, "Nkulumane")
    offering_worker = await worker_factory(TradeEnum.PLUMBING, "Nkulumane")
    job = await _create_job(client, buyer)

    await client.post(
        f"/jobs/{job['id']}/offers",
        json={"quoted_amount": "35.00"},
        headers=auth_headers(offering_worker),
    )

    response = await client.get(f"/jobs/{job['id']}/matches", headers=auth_headers(buyer))

    assert response.status_code == 200
    candidates = response.json()
    returned_ids = [candidate["worker_id"] for candidate in candidates]
    assert str(offering_worker.id) in returned_ids
    assert len(returned_ids) == 4
    assert returned_ids[0] == str(offering_worker.id)
    assert {str(best.id), str(second.id), str(third.id)}.issubset(returned_ids)


async def test_matches_have_null_offer_fields_when_no_offer_submitted(
    client, buyer, worker_factory
):
    await worker_factory(TradeEnum.PLUMBING, "Nkulumane")
    job = await _create_job(client, buyer)

    response = await client.get(f"/jobs/{job['id']}/matches", headers=auth_headers(buyer))

    assert response.status_code == 200
    candidates = response.json()
    assert len(candidates) == 1
    assert candidates[0]["quoted_amount"] is None
    assert candidates[0]["availability_note"] is None
    assert candidates[0]["quoted_at"] is None


async def test_worker_sees_open_jobs_in_their_trade_and_range(client, buyer, worker_factory):
    worker = await worker_factory(TradeEnum.PLUMBING, "Nkulumane")
    matching_job = await _create_job(client, buyer, budget_amount="40.00")
    await _create_job(client, buyer, trade="ELECTRICAL")

    response = await client.get("/jobs/open", headers=auth_headers(worker))

    assert response.status_code == 200
    jobs = response.json()
    assert len(jobs) == 1
    assert jobs[0]["job_id"] == matching_job["id"]
    assert jobs[0]["budget_amount"] == "40.00"
    assert jobs[0]["distance_band"] == "SAME_SUBURB"


async def test_worker_open_jobs_excludes_far_suburb(client, buyer, worker_factory):
    # Hillside is ~10.7km from Nkulumane in the seeded suburb coordinates: FAR.
    worker = await worker_factory(TradeEnum.PLUMBING, "Hillside")
    await _create_job(client, buyer)

    response = await client.get("/jobs/open", headers=auth_headers(worker))

    assert response.status_code == 200
    assert response.json() == []


async def test_worker_open_jobs_excludes_jobs_no_longer_open(client, buyer, worker_factory):
    worker = await worker_factory(TradeEnum.PLUMBING, "Nkulumane")
    other_worker = await worker_factory(TradeEnum.PLUMBING, "Nkulumane")
    job = await _create_job(client, buyer)
    await client.get(f"/jobs/{job['id']}/matches", headers=auth_headers(buyer))
    await client.post(
        f"/jobs/{job['id']}/book",
        json={"worker_id": str(other_worker.id), "deposit_amount": "50.00"},
        headers=auth_headers(buyer),
    )

    response = await client.get("/jobs/open", headers=auth_headers(worker))

    assert response.status_code == 200
    assert response.json() == []


async def test_open_jobs_requires_worker_role(client, buyer):
    await _create_job(client, buyer)

    response = await client.get("/jobs/open", headers=auth_headers(buyer))

    assert response.status_code == 403


async def test_job_request_accepts_optional_budget_amount(client, buyer):
    job = await _create_job(client, buyer, budget_amount="40.00")

    assert job["budget_amount"] == "40.00"
