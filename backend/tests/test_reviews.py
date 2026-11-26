"""ADR-011: two-way, double-blind reviews after sign-off."""

from datetime import timedelta
from decimal import Decimal

import pytest

from app.apps.reviews.domain import services as review_services
from app.apps.reviews.domain.rules import summarize, weighted_score
from app.shared_kernel.clock import utcnow
from app.shared_kernel.enums import ReviewTagEnum, TradeEnum
from tests.conftest import auth_headers


async def _completed_job(client, buyer, worker) -> str:
    job = await client.post(
        "/jobs/request",
        headers=auth_headers(buyer),
        json={
            "trade": "PLUMBING",
            "suburb": "Hillside",
            "address": "14 Harrow Rd",
            "problem_description": "Leaking tap",
        },
    )
    job_id = str(job.json()["id"])
    await client.get(f"/jobs/{job_id}/matches", headers=auth_headers(buyer))
    await client.post(
        f"/jobs/{job_id}/book",
        headers=auth_headers(buyer),
        json={"worker_id": str(worker.id), "deposit_amount": "10.00"},
    )
    await client.post(
        f"/jobs/{job_id}/quote",
        headers=auth_headers(worker),
        json={"labor_amount": "30.00", "materials_amount": "10.00"},
    )
    done = await client.post(
        f"/jobs/{job_id}/complete",
        headers=auth_headers(buyer),
        json={"what_was_done": "Replaced tap washer"},
    )
    assert done.status_code == 200, done.text
    return job_id


async def _review(client, person, job_id: str, rating: int, tags: list[str], comment=None):
    body: dict[str, object] = {"rating": rating, "tags": tags}
    if comment is not None:
        body["comment"] = comment
    return await client.post(f"/jobs/{job_id}/review", headers=auth_headers(person), json=body)


@pytest.fixture
async def setup(client, buyer, worker_factory):
    worker = await worker_factory(TradeEnum.PLUMBING, "Hillside")
    job_id = await _completed_job(client, buyer, worker)
    return worker, job_id


def _travel(monkeypatch: pytest.MonkeyPatch, days: int) -> None:
    later = utcnow() + timedelta(days=days)
    monkeypatch.setattr(review_services, "utcnow", lambda: later)


# ---- pure rules -------------------------------------------------------------


def test_weighted_score_pulls_small_samples_towards_the_prior():
    assert weighted_score(5, 1) == Decimal("4.2")  # one 5-star review
    assert weighted_score(0, 0) is None
    many = weighted_score(48 * 5, 48)
    assert many is not None and many > Decimal("4.8")


def test_summary_marks_fewer_than_three_reviews_as_new():
    summary = summarize([5, 4], [[ReviewTagEnum.ON_TIME], [ReviewTagEnum.ON_TIME]])
    assert summary.is_new is True
    assert summary.average == Decimal("4.5")
    assert summary.tag_counts == {"ON_TIME": 2}


# ---- submitting ---------------------------------------------------------------


async def test_both_sides_review_and_see_each_other_only_after_both(client, buyer, setup):
    worker, job_id = setup

    first = await _review(client, buyer, job_id, 5, ["ON_TIME"], "Fast and tidy")
    assert first.status_code == 201
    assert first.json()["published_at"] is None

    worker_view = (await client.get(f"/jobs/{job_id}/reviews", headers=auth_headers(worker))).json()
    assert worker_view["theirs"] is None
    assert worker_view["is_theirs_waiting"] is True
    assert worker_view["can_review"] is True
    public = (await client.get(f"/workers/{worker.id}/reviews", headers=auth_headers(buyer))).json()
    assert public["summary"]["count"] == 0

    second = await _review(client, worker, job_id, 4, ["PAID_ON_TIME", "RESPECTFUL"])
    assert second.status_code == 201
    assert second.json()["published_at"] is not None

    buyer_view = (await client.get(f"/jobs/{job_id}/reviews", headers=auth_headers(buyer))).json()
    assert buyer_view["theirs"]["rating"] == 4
    assert buyer_view["mine"]["published_at"] is not None
    public = (await client.get(f"/workers/{worker.id}/reviews", headers=auth_headers(buyer))).json()
    assert public["summary"]["count"] == 1
    assert public["summary"]["is_new"] is True
    assert public["reviews"][0]["comment"] == "Fast and tidy"
    assert public["reviews"][0]["trade"] == "PLUMBING"


async def test_a_lone_review_shows_after_the_window(client, buyer, setup, monkeypatch):
    worker, job_id = setup
    await _review(client, buyer, job_id, 3, ["FAIR_PRICE"])

    _travel(monkeypatch, 15)

    public = (await client.get(f"/workers/{worker.id}/reviews", headers=auth_headers(buyer))).json()
    assert public["summary"]["count"] == 1
    late = await _review(client, worker, job_id, 5, ["PAID_ON_TIME"])
    assert late.status_code == 409


async def test_reviewing_twice_or_before_completion_is_refused(client, buyer, worker_factory):
    worker = await worker_factory(TradeEnum.PLUMBING, "Hillside")
    job = await client.post(
        "/jobs/request",
        headers=auth_headers(buyer),
        json={
            "trade": "PLUMBING",
            "suburb": "Hillside",
            "address": "1 A Rd",
            "problem_description": "Leaking tap",
        },
    )
    early = await _review(client, buyer, str(job.json()["id"]), 5, [])
    assert early.status_code == 409

    job_id = await _completed_job(client, buyer, worker)
    assert (await _review(client, buyer, job_id, 5, [])).status_code == 201
    assert (await _review(client, buyer, job_id, 4, [])).status_code == 409


async def test_tags_must_fit_the_direction(client, buyer, setup):
    worker, job_id = setup

    wrong_for_worker = await _review(client, worker, job_id, 5, ["QUALITY_WORK"])
    wrong_for_buyer = await _review(client, buyer, job_id, 5, ["PAID_ON_TIME"])

    assert wrong_for_worker.status_code == 422
    assert wrong_for_buyer.status_code == 422


async def test_outsiders_cannot_review_or_read_a_jobs_reviews(client, other_buyer, setup):
    _, job_id = setup

    assert (await _review(client, other_buyer, job_id, 1, [])).status_code == 404
    response = await client.get(f"/jobs/{job_id}/reviews", headers=auth_headers(other_buyer))
    assert response.status_code == 404


# ---- ratings follow visibility -------------------------------------------------


async def test_worker_rating_counts_only_visible_reviews(client, buyer, setup):
    worker, job_id = setup
    await _review(client, buyer, job_id, 5, [])

    profile = (await client.get(f"/workers/{worker.id}", headers=auth_headers(buyer))).json()
    assert profile["rating_count"] == 0

    await _review(client, worker, job_id, 5, [])
    profile = (await client.get(f"/workers/{worker.id}", headers=auth_headers(buyer))).json()
    assert profile["rating_count"] == 1


async def test_workers_can_see_what_others_said_about_a_client(
    client, buyer, setup, worker_factory
):
    worker, job_id = setup
    await _review(client, buyer, job_id, 5, [])
    await _review(client, worker, job_id, 2, ["JOB_AS_DESCRIBED"], "Paid late")
    new_job = await client.post(
        "/jobs/request",
        headers=auth_headers(buyer),
        json={
            "trade": "PLUMBING",
            "suburb": "Hillside",
            "address": "2 B Rd",
            "problem_description": "Blocked drain",
        },
    )
    stranger = await worker_factory(TradeEnum.PLUMBING, "Hillside")

    response = await client.get(
        f"/jobs/{new_job.json()['id']}/client-reviews", headers=auth_headers(stranger)
    )

    assert response.status_code == 200
    body = response.json()
    assert body["summary"]["count"] == 1
    assert body["reviews"][0]["comment"] == "Paid late"
    assert str(buyer.id) not in str(body)


# ---- reply, report, moderation -------------------------------------------------


async def _published_review_id(client, buyer, worker, job_id) -> str:
    await _review(client, buyer, job_id, 2, ["ON_TIME"], "Came late")
    await _review(client, worker, job_id, 5, [])
    view = (await client.get(f"/jobs/{job_id}/reviews", headers=auth_headers(worker))).json()
    return str(view["theirs"]["id"])


async def test_the_person_reviewed_can_reply_once(client, buyer, setup):
    worker, job_id = setup
    review_id = await _published_review_id(client, buyer, worker, job_id)

    first = await client.post(
        f"/reviews/{review_id}/reply",
        headers=auth_headers(worker),
        json={"reply": "Sorry, the kombi broke down."},
    )
    again = await client.post(
        f"/reviews/{review_id}/reply", headers=auth_headers(worker), json={"reply": "Again"}
    )
    by_author = await client.post(
        f"/reviews/{review_id}/reply", headers=auth_headers(buyer), json={"reply": "No"}
    )

    assert first.status_code == 200
    assert again.status_code == 409
    assert by_author.status_code == 403
    public = (await client.get(f"/workers/{worker.id}/reviews", headers=auth_headers(buyer))).json()
    assert public["reviews"][0]["reply"] == "Sorry, the kombi broke down."


async def test_a_report_keeps_the_review_up_until_ops_removes_it(client, buyer, setup, ops_user):
    worker, job_id = setup
    review_id = await _published_review_id(client, buyer, worker, job_id)

    report = await client.post(
        f"/reviews/{review_id}/report",
        headers=auth_headers(worker),
        json={"reason": "This was a different job"},
    )
    assert report.status_code == 200
    public = (await client.get(f"/workers/{worker.id}/reviews", headers=auth_headers(buyer))).json()
    assert public["summary"]["count"] == 1

    queue = await client.get("/ops/reviews/reported", headers=auth_headers(ops_user))
    assert [row["review_id"] for row in queue.json()] == [review_id]
    assert (
        await client.get("/ops/reviews/reported", headers=auth_headers(worker))
    ).status_code == 403

    removed = await client.post(
        f"/ops/reviews/{review_id}/moderate",
        headers=auth_headers(ops_user),
        json={"decision": "REMOVE"},
    )
    assert removed.status_code == 200
    public = (await client.get(f"/workers/{worker.id}/reviews", headers=auth_headers(buyer))).json()
    assert public["summary"]["count"] == 0
    queue = await client.get("/ops/reviews/reported", headers=auth_headers(ops_user))
    assert queue.json() == []
