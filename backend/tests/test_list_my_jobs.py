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


async def test_buyer_sees_only_their_own_jobs_newest_first(client, buyer, other_buyer):
    first = await _create_job(client, buyer, problem_description="First leak")
    second = await _create_job(client, buyer, problem_description="Second leak")
    await _create_job(client, other_buyer, problem_description="Someone else's job")

    response = await client.get("/jobs/mine", headers=auth_headers(buyer))

    assert response.status_code == 200
    jobs = response.json()
    assert [j["id"] for j in jobs] == [second["id"], first["id"]]


async def test_offer_count_reflects_submitted_offers(client, buyer, worker_factory):
    worker = await worker_factory(TradeEnum.PLUMBING, "Nkulumane")
    other_worker = await worker_factory(TradeEnum.PLUMBING, "Nkulumane")
    job = await _create_job(client, buyer)

    await client.post(
        f"/jobs/{job['id']}/offers",
        json={"quoted_amount": "30.00"},
        headers=auth_headers(worker),
    )
    await client.post(
        f"/jobs/{job['id']}/offers",
        json={"quoted_amount": "25.00"},
        headers=auth_headers(other_worker),
    )

    response = await client.get("/jobs/mine", headers=auth_headers(buyer))

    assert response.status_code == 200
    jobs = response.json()
    assert len(jobs) == 1
    assert jobs[0]["offer_count"] == 2


async def test_job_with_no_offers_has_zero_count(client, buyer):
    await _create_job(client, buyer)

    response = await client.get("/jobs/mine", headers=auth_headers(buyer))

    assert response.json()[0]["offer_count"] == 0


async def test_list_my_jobs_requires_buyer_role(client, worker):
    response = await client.get("/jobs/mine", headers=auth_headers(worker))

    assert response.status_code == 403
