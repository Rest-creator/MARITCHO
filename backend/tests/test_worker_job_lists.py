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


async def _book(client, buyer, job, worker):
    await client.get(f"/jobs/{job['id']}/matches", headers=auth_headers(buyer))
    response = await client.post(
        f"/jobs/{job['id']}/book",
        json={"worker_id": str(worker.id), "deposit_amount": "50.00"},
        headers=auth_headers(buyer),
    )
    assert response.status_code == 200
    return response.json()


async def test_assigned_jobs_only_shows_this_workers_own_jobs(
    client, buyer, worker_factory
):
    worker = await worker_factory(TradeEnum.PLUMBING, "Nkulumane")
    other_worker = await worker_factory(TradeEnum.PLUMBING, "Nkulumane")
    job = await _create_job(client, buyer)
    await _book(client, buyer, job, worker)
    await _create_job(client, buyer, problem_description="Someone else's job")

    response = await client.get("/jobs/assigned", headers=auth_headers(worker))

    assert response.status_code == 200
    jobs = response.json()
    assert len(jobs) == 1
    assert jobs[0]["id"] == job["id"]

    other_response = await client.get("/jobs/assigned", headers=auth_headers(other_worker))
    assert other_response.json() == []


async def test_assigned_jobs_requires_worker_role(client, buyer):
    response = await client.get("/jobs/assigned", headers=auth_headers(buyer))

    assert response.status_code == 403


async def test_my_offers_shows_only_this_workers_offers_with_job_context(
    client, buyer, worker_factory
):
    worker = await worker_factory(TradeEnum.PLUMBING, "Nkulumane")
    other_worker = await worker_factory(TradeEnum.PLUMBING, "Nkulumane")
    job = await _create_job(client, buyer)

    await client.post(
        f"/jobs/{job['id']}/offers",
        json={"quoted_amount": "35.00", "availability_note": "I can come at 2pm"},
        headers=auth_headers(worker),
    )
    await client.post(
        f"/jobs/{job['id']}/offers",
        json={"quoted_amount": "25.00"},
        headers=auth_headers(other_worker),
    )

    response = await client.get("/jobs/my-offers", headers=auth_headers(worker))

    assert response.status_code == 200
    offers = response.json()
    assert len(offers) == 1
    assert offers[0]["job_id"] == job["id"]
    assert offers[0]["quoted_amount"] == "35.00"
    assert offers[0]["availability_note"] == "I can come at 2pm"
    assert offers[0]["job_trade"] == "PLUMBING"
    assert offers[0]["job_suburb"] == "Nkulumane"
    assert offers[0]["job_status"] == "REQUESTED"


async def test_my_offers_requires_worker_role(client, buyer):
    response = await client.get("/jobs/my-offers", headers=auth_headers(buyer))

    assert response.status_code == 403
