"""Restrict jobs to matching skills, end to end (search, list, view, offer)."""

import logging

from app.shared_kernel.enums import TradeEnum
from tests.conftest import auth_headers

PLUMBING_JOB = {
    "trade": "PLUMBING",
    "suburb": "Hillside",
    "address": "14 Harrow Rd",
    "problem_description": "Burst hot water geyser pipe flooding the bathroom floor",
    "budget_amount": "45.00",
    "needed_by": "TODAY",
}


async def _post_job(client, buyer, payload: dict[str, str]) -> str:
    response = await client.post("/jobs/request", headers=auth_headers(buyer), json=payload)
    assert response.status_code == 201, response.text
    return response.json()["id"]


async def test_solar_worker_cannot_offer_on_plumbing_and_the_denial_is_audited(
    client, buyer, worker_factory, caplog
):
    job_id = await _post_job(client, buyer, PLUMBING_JOB)
    solar = await worker_factory(TradeEnum.SOLAR, "Hillside")

    with caplog.at_level(logging.WARNING, logger="maricho-api"):
        response = await client.post(
            f"/jobs/{job_id}/offers",
            headers=auth_headers(solar),
            json={"quoted_amount": "40.00", "availability_note": "Today"},
        )

    assert response.status_code == 422
    assert "needs plumbing" in response.json()["detail"]
    assert "solar installation" in response.json()["detail"]
    audits = [r.audit for r in caplog.records if getattr(r, "audit", None)]
    assert any(
        a["event"] == "job_eligibility_denied" and a["action"] == "OFFER" and a["job_id"] == job_id
        for a in audits
    )


async def test_plumber_can_offer_on_plumbing(client, buyer, worker_factory):
    job_id = await _post_job(client, buyer, PLUMBING_JOB)
    plumber = await worker_factory(TradeEnum.PLUMBING, "Hillside")

    response = await client.post(
        f"/jobs/{job_id}/offers",
        headers=auth_headers(plumber),
        json={"quoted_amount": "40.00", "availability_note": "Today"},
    )
    assert response.status_code == 201


async def test_worker_search_only_returns_jobs_matching_their_skills(client, buyer, worker_factory):
    job_id = await _post_job(client, buyer, PLUMBING_JOB)
    solar = await worker_factory(TradeEnum.SOLAR, "Hillside")
    plumber = await worker_factory(TradeEnum.PLUMBING, "Hillside")
    params = {"q": "geyser pipe leaking bathroom"}

    buyer_hits = (
        await client.get("/jobs/search", params=params, headers=auth_headers(buyer))
    ).json()
    solar_hits = (
        await client.get("/jobs/search", params=params, headers=auth_headers(solar))
    ).json()
    plumber_hits = (
        await client.get("/jobs/search", params=params, headers=auth_headers(plumber))
    ).json()

    assert job_id in {hit["job_id"] for hit in buyer_hits}
    assert solar_hits == []
    assert job_id in {hit["job_id"] for hit in plumber_hits}

    # Asking for another trade explicitly doesn't get around it either.
    forced = await client.get(
        "/jobs/search", params={**params, "trade": "PLUMBING"}, headers=auth_headers(solar)
    )
    assert forced.json() == []


async def test_eligibility_endpoint_explains_a_mismatch(client, buyer, worker_factory, caplog):
    job_id = await _post_job(client, buyer, PLUMBING_JOB)
    solar = await worker_factory(TradeEnum.SOLAR, "Hillside")
    plumber = await worker_factory(TradeEnum.PLUMBING, "Hillside")

    ok = await client.get(f"/jobs/{job_id}/eligibility", headers=auth_headers(plumber))
    assert ok.status_code == 200
    assert ok.json()["is_eligible"] is True
    assert ok.json()["matched_by"] == "TRADE"

    with caplog.at_level(logging.WARNING, logger="maricho-api"):
        denied = await client.get(f"/jobs/{job_id}/eligibility", headers=auth_headers(solar))
    assert denied.status_code == 200
    body = denied.json()
    assert body["is_eligible"] is False
    assert body["required_trade"] == "PLUMBING"
    assert "isn't one of your skills" in body["reason"]
    assert any(getattr(r, "audit", {}).get("action") == "VIEW" for r in caplog.records)

    as_buyer = await client.get(f"/jobs/{job_id}/eligibility", headers=auth_headers(buyer))
    assert as_buyer.status_code == 403


async def test_clear_general_maintenance_job_reaches_the_matching_specialist(
    client, buyer, worker_factory
):
    job_id = await _post_job(
        client,
        buyer,
        {
            **PLUMBING_JOB,
            "trade": "GENERAL_MAINTENANCE",
            "problem_description": "Geyser leaking in the bathroom, water everywhere",
        },
    )
    plumber = await worker_factory(TradeEnum.PLUMBING, "Hillside")
    painter = await worker_factory(TradeEnum.PAINTING, "Hillside")

    plumber_open = (await client.get("/jobs/open", headers=auth_headers(plumber))).json()
    painter_open = (await client.get("/jobs/open", headers=auth_headers(painter))).json()
    assert job_id in {item["job_id"] for item in plumber_open}
    assert job_id not in {item["job_id"] for item in painter_open}

    eligibility = (
        await client.get(f"/jobs/{job_id}/eligibility", headers=auth_headers(plumber))
    ).json()
    assert eligibility["matched_by"] == "SIMILARITY"

    offer = await client.post(
        f"/jobs/{job_id}/offers",
        headers=auth_headers(plumber),
        json={"quoted_amount": "40.00", "availability_note": "Today"},
    )
    assert offer.status_code == 201


async def test_vague_general_job_stays_with_general_maintenance_workers(
    client, buyer, worker_factory
):
    job_id = await _post_job(
        client,
        buyer,
        {
            **PLUMBING_JOB,
            "trade": "GENERAL_MAINTENANCE",
            "problem_description": "Help with odd jobs",
        },
    )
    handyman = await worker_factory(TradeEnum.GENERAL_MAINTENANCE, "Hillside")
    plumber = await worker_factory(TradeEnum.PLUMBING, "Hillside")

    assert job_id in {
        item["job_id"]
        for item in (await client.get("/jobs/open", headers=auth_headers(handyman))).json()
    }
    assert job_id not in {
        item["job_id"]
        for item in (await client.get("/jobs/open", headers=auth_headers(plumber))).json()
    }
