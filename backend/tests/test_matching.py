import uuid
from decimal import Decimal

from app.models import GradeEnum, Job, JobStatusEnum, TradeEnum
from tests.conftest import auth_headers

JOB_PAYLOAD = {
    "trade": "PLUMBING",
    "suburb": "Nkulumane",
    "address": "12 Fife Street, Nkulumane",
    "problem_description": "Leaking geyser in the bathroom, water on the floor.",
}


async def _create_job(client, buyer):
    response = await client.post("/jobs/request", json=JOB_PAYLOAD, headers=auth_headers(buyer))
    assert response.status_code == 201
    return response.json()


async def test_matching_returns_eligible_worker(client, buyer, worker_factory):
    await worker_factory(TradeEnum.PLUMBING, "Nkulumane")
    job = await _create_job(client, buyer)

    response = await client.get(f"/jobs/{job['id']}/matches", headers=auth_headers(buyer))

    assert response.status_code == 200
    candidates = response.json()
    assert len(candidates) == 1
    assert candidates[0]["reason"]


async def test_matching_excludes_wrong_trade(client, buyer, worker_factory):
    await worker_factory(TradeEnum.ELECTRICAL, "Nkulumane")
    job = await _create_job(client, buyer)

    response = await client.get(f"/jobs/{job['id']}/matches", headers=auth_headers(buyer))

    assert response.status_code == 200
    assert response.json() == []


async def test_matching_excludes_far_suburb_worker(client, buyer, worker_factory):
    # Hillside is ~10.7km from Nkulumane in the seeded suburb coordinates: FAR.
    await worker_factory(TradeEnum.PLUMBING, "Hillside")
    job = await _create_job(client, buyer)

    response = await client.get(f"/jobs/{job['id']}/matches", headers=auth_headers(buyer))

    assert response.status_code == 200
    assert response.json() == []


async def test_matching_includes_nearby_suburb_worker(client, buyer, worker_factory):
    # Njube is ~1.5km from Nkulumane: NEARBY, should still match.
    nearby_worker = await worker_factory(TradeEnum.PLUMBING, "Njube")
    job = await _create_job(client, buyer)

    response = await client.get(f"/jobs/{job['id']}/matches", headers=auth_headers(buyer))

    assert response.status_code == 200
    candidates = response.json()
    assert len(candidates) == 1
    assert candidates[0]["worker_id"] == str(nearby_worker.id)
    assert candidates[0]["distance_band"] == "NEARBY"


async def test_matching_includes_moderate_suburb_worker(client, buyer, worker_factory):
    # Luveve is ~5.6km from Nkulumane: MODERATE, should still match.
    moderate_worker = await worker_factory(TradeEnum.PLUMBING, "Luveve")
    job = await _create_job(client, buyer)

    response = await client.get(f"/jobs/{job['id']}/matches", headers=auth_headers(buyer))

    assert response.status_code == 200
    candidates = response.json()
    assert len(candidates) == 1
    assert candidates[0]["worker_id"] == str(moderate_worker.id)
    assert candidates[0]["distance_band"] == "MODERATE"


async def test_matching_ranks_closer_band_above_farther_better_standing(
    client, buyer, worker_factory
):
    # A NEARBY worker with weak standing should still outrank a MODERATE
    # worker with excellent standing: distance band is the primary sort key.
    nearby_weak = await worker_factory(
        TradeEnum.PLUMBING, "Njube", grade=GradeEnum.REGISTERED, on_time_rate=Decimal("60.00")
    )
    moderate_strong = await worker_factory(
        TradeEnum.PLUMBING, "Luveve", grade=GradeEnum.EXPERT, on_time_rate=Decimal("99.00")
    )

    job = await _create_job(client, buyer)

    response = await client.get(f"/jobs/{job['id']}/matches", headers=auth_headers(buyer))

    assert response.status_code == 200
    candidates = response.json()
    returned_ids = [c["worker_id"] for c in candidates]
    assert returned_ids == [str(nearby_weak.id), str(moderate_strong.id)]


async def test_matching_excludes_busy_worker(client, buyer, worker_factory, db_session):
    busy_worker = await worker_factory(TradeEnum.PLUMBING, "Nkulumane")
    db_session.add(
        Job(
            buyer_id=buyer.id,
            worker_id=busy_worker.id,
            status=JobStatusEnum.BOOKED,
            trade=TradeEnum.PLUMBING,
            suburb="Nkulumane",
            address="12 Fife Street, Nkulumane",
        )
    )
    await db_session.commit()

    job = await _create_job(client, buyer)

    response = await client.get(f"/jobs/{job['id']}/matches", headers=auth_headers(buyer))

    assert response.status_code == 200
    assert response.json() == []


async def test_matching_ranks_by_standing_and_caps_at_three(client, buyer, worker_factory):
    worst = await worker_factory(
        TradeEnum.PLUMBING, "Nkulumane", grade=GradeEnum.REGISTERED, on_time_rate=Decimal("60.00")
    )
    best = await worker_factory(
        TradeEnum.PLUMBING, "Nkulumane", grade=GradeEnum.EXPERT, on_time_rate=Decimal("99.00")
    )
    mid = await worker_factory(
        TradeEnum.PLUMBING, "Nkulumane", grade=GradeEnum.JOURNEYMAN, on_time_rate=Decimal("80.00")
    )
    await worker_factory(
        TradeEnum.PLUMBING, "Nkulumane", grade=GradeEnum.REGISTERED, on_time_rate=Decimal("50.00")
    )

    job = await _create_job(client, buyer)

    response = await client.get(f"/jobs/{job['id']}/matches", headers=auth_headers(buyer))

    assert response.status_code == 200
    candidates = response.json()
    assert len(candidates) == 3
    returned_ids = [c["worker_id"] for c in candidates]
    assert returned_ids == [str(best.id), str(mid.id), str(worst.id)]


async def test_matching_transitions_job_status_to_matched(client, buyer, worker_factory):
    await worker_factory(TradeEnum.PLUMBING, "Nkulumane")
    job = await _create_job(client, buyer)
    assert job["status"] == "REQUESTED"

    await client.get(f"/jobs/{job['id']}/matches", headers=auth_headers(buyer))

    fetched = await client.get(f"/jobs/{job['id']}", headers=auth_headers(buyer))
    assert fetched.json()["status"] == "MATCHED"


async def test_matching_on_booked_job_returns_409(client, buyer, worker_factory, db_session):
    matched_worker = await worker_factory(TradeEnum.PLUMBING, "Nkulumane")
    job = await _create_job(client, buyer)

    db_job = await db_session.get(Job, uuid.UUID(job["id"]))
    db_job.status = JobStatusEnum.BOOKED
    db_job.worker_id = matched_worker.id
    await db_session.commit()

    response = await client.get(f"/jobs/{job['id']}/matches", headers=auth_headers(buyer))

    assert response.status_code == 409


async def test_matching_forbidden_for_other_buyer(client, buyer, other_buyer):
    job = await _create_job(client, buyer)

    response = await client.get(f"/jobs/{job['id']}/matches", headers=auth_headers(other_buyer))

    assert response.status_code == 403


async def test_matching_forbidden_for_worker_role(client, buyer, worker):
    job = await _create_job(client, buyer)

    response = await client.get(f"/jobs/{job['id']}/matches", headers=auth_headers(worker))

    assert response.status_code == 403


async def test_matching_requires_authentication(client, buyer):
    job = await _create_job(client, buyer)

    response = await client.get(f"/jobs/{job['id']}/matches")

    assert response.status_code == 401


async def test_matching_missing_job_returns_404(client, buyer):
    missing_id = "00000000-0000-0000-0000-000000000000"

    response = await client.get(f"/jobs/{missing_id}/matches", headers=auth_headers(buyer))

    assert response.status_code == 404
