from decimal import Decimal

from sqlalchemy import select

from app.apps.jobs.infrastructure.models import JobModel
from app.shared_kernel.embeddings import (
    EMBEDDING_DIM,
    cosine_similarity,
    embed_text,
    infer_best_trade,
    rank_skills_by_query,
)
from app.shared_kernel.enums import TradeEnum
from tests.conftest import auth_headers


def test_embeddings_are_normalized_and_semantically_coherent():
    plumbing_vec = embed_text("Geyser is leaking water and bathroom pipe burst")
    plumbing_shona = embed_text("Pombi yemvura iri kudonha muchimbuzi")
    solar_vec = embed_text("Solar panels and lithium inverter battery not charging")

    assert len(plumbing_vec) == EMBEDDING_DIM
    assert abs(sum(x * x for x in plumbing_vec) - 1.0) < 1e-4

    sim_plumbing = cosine_similarity(plumbing_vec, plumbing_shona)
    sim_cross = cosine_similarity(plumbing_vec, solar_vec)
    assert sim_plumbing > 0.5
    assert sim_plumbing > sim_cross

    trade, score = infer_best_trade("I need someone to weld a sliding gate and burglar bars")
    assert trade == TradeEnum.WELDING
    assert score > 0.4

    skills = rank_skills_by_query("fridge not cooling and stove broken")
    assert skills[0].trade == TradeEnum.APPLIANCE_REPAIR


async def test_pgvector_job_search_ranks_semantically_matching_jobs_first(
    client, buyer, worker_factory, db_session
):
    # Create three open jobs in different trades
    plumbing_res = await client.post(
        "/jobs/request",
        headers=auth_headers(buyer),
        json={
            "trade": "PLUMBING",
            "suburb": "Hillside",
            "address": "14 Harrow Rd",
            "problem_description": "Burst hot water geyser pipe flooding the bathroom floor",
            "budget_amount": "45.00",
            "needed_by": "TODAY",
        },
    )
    assert plumbing_res.status_code == 201
    plumbing_id = plumbing_res.json()["id"]

    solar_res = await client.post(
        "/jobs/request",
        headers=auth_headers(buyer),
        json={
            "trade": "SOLAR",
            "suburb": "Kumalo",
            "address": "8 Park Rd",
            "problem_description": "5kVA solar inverter beeping and lithium battery not charging",
            "budget_amount": "80.00",
            "needed_by": "THIS_WEEK",
        },
    )
    assert solar_res.status_code == 201
    solar_id = solar_res.json()["id"]

    welding_res = await client.post(
        "/jobs/request",
        headers=auth_headers(buyer),
        json={
            "trade": "WELDING",
            "suburb": "Luveve",
            "address": "3 Main St",
            "problem_description": "Fabricate and weld steel burglar bars and sliding gate",
            "budget_amount": "120.00",
        },
    )
    assert welding_res.status_code == 201

    # Verify pgvector column is populated in PostgreSQL
    stored = await db_session.scalar(select(JobModel).where(JobModel.id == plumbing_id))
    assert stored is not None
    assert stored.problem_embedding is not None
    assert len(stored.problem_embedding) == EMBEDDING_DIM

    # Search for water/leak issues via pgvector endpoint
    search_plumbing = await client.get(
        "/jobs/search",
        params={"q": "leaking tap and water pipe"},
        headers=auth_headers(buyer),
    )
    assert search_plumbing.status_code == 200
    hits = search_plumbing.json()
    assert len(hits) >= 1
    assert hits[0]["job_id"] == plumbing_id
    assert hits[0]["trade"] == "PLUMBING"
    assert hits[0]["needed_by"] == "TODAY"
    assert hits[0]["similarity_score"] > 0.3

    # Search for solar battery issues
    search_solar = await client.get(
        "/jobs/search",
        params={"q": "solar panel battery backup"},
        headers=auth_headers(buyer),
    )
    assert search_solar.status_code == 200
    solar_hits = search_solar.json()
    assert len(solar_hits) >= 1
    assert solar_hits[0]["job_id"] == solar_id

    # Filter by trade and suburb
    filtered = await client.get(
        "/jobs/search",
        params={"q": "repair", "trade": "SOLAR", "suburb": "Kumalo"},
        headers=auth_headers(buyer),
    )
    assert filtered.status_code == 200
    assert all(item["trade"] == "SOLAR" and item["suburb"] == "Kumalo" for item in filtered.json())

    # Worker open jobs endpoint with pgvector `q` filter
    plumber_worker = await worker_factory(TradeEnum.PLUMBING, "Hillside")
    open_filtered = await client.get(
        "/jobs/open",
        params={"q": "geyser bathroom"},
        headers=auth_headers(plumber_worker),
    )
    assert open_filtered.status_code == 200
    open_items = open_filtered.json()
    assert len(open_items) == 1
    assert open_items[0]["job_id"] == plumbing_id
    assert open_items[0]["similarity_score"] is not None


async def test_semantic_skill_search_endpoint(client):
    res = await client.get("/jobs/search/skills", params={"q": "wiring plug sockets and lights"})
    assert res.status_code == 200
    skills = res.json()
    assert len(skills) >= 1
    assert skills[0]["id"] == "electrician"
    assert skills[0]["trade"] == "ELECTRICAL"
    assert skills[0]["similarity_score"] > 0.3


async def test_signup_then_patch_profile_fields(client):
    phone = "+263779888777"
    signup_res = await client.post(
        "/auth/signup",
        json={"phone": phone, "password": "correct-horse", "name": "Tendai Moyo", "role": "WORKER"},
    )
    assert signup_res.status_code == 200
    token = signup_res.json()["access_token"]

    # Update profile via PATCH /users/me
    patch_res = await client.patch(
        "/users/me",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "display_name": "Tendai Moyo",
            "is_available": True,
            "travel_km": 25,
            "home_suburb": "Hillside",
        },
    )
    assert patch_res.status_code == 200
    user_data = patch_res.json()
    assert user_data["display_name"] == "Tendai Moyo"
    assert user_data["travel_km"] == 25
    assert user_data["home_suburb"] == "Hillside"


async def test_media_upload_webm_voice_then_owner_can_download(client, buyer):
    # Upload audio/webm;codecs=opus as buyer
    upload_res = await client.post(
        "/media/upload",
        headers={**auth_headers(buyer), "Idempotency-Key": "voice-note-12345"},
        files={"file": ("voice-note.webm", b"WEBM_OPUS_BYTES", "audio/webm;codecs=opus")},
    )
    assert upload_res.status_code == 201
    media_url = upload_res.json()["url"]
    assert media_url.startswith("/media/")
    assert upload_res.json()["content_type"] == "audio/webm"

    # The owner can download their own media
    download_res = await client.get(media_url, headers=auth_headers(buyer))
    assert download_res.status_code == 200
    assert download_res.content == b"WEBM_OPUS_BYTES"


async def test_media_download_rejects_unrelated_user(client, buyer, worker):
    upload_res = await client.post(
        "/media/upload",
        headers={**auth_headers(buyer), "Idempotency-Key": "voice-note-67890"},
        files={"file": ("voice-note.webm", b"WEBM_OPUS_BYTES", "audio/webm;codecs=opus")},
    )
    assert upload_res.status_code == 201
    media_url = upload_res.json()["url"]

    # A worker with no relationship to this media must not be able to fetch it
    download_res = await client.get(media_url, headers=auth_headers(worker))
    assert download_res.status_code == 404


async def test_media_download_allows_ops_role(client, buyer, ops_user):
    upload_res = await client.post(
        "/media/upload",
        headers={**auth_headers(buyer), "Idempotency-Key": "voice-note-ops"},
        files={"file": ("voice-note.webm", b"WEBM_OPUS_BYTES", "audio/webm;codecs=opus")},
    )
    assert upload_res.status_code == 201
    media_url = upload_res.json()["url"]

    download_res = await client.get(media_url, headers=auth_headers(ops_user))
    assert download_res.status_code == 200
    assert download_res.content == b"WEBM_OPUS_BYTES"


async def test_completed_job_review_updates_worker_standing(
    client, buyer, worker_factory
):
    skilled_worker = await worker_factory(TradeEnum.PLUMBING, "Hillside")
    job_res = await client.post(
        "/jobs/request",
        headers=auth_headers(buyer),
        json={
            "trade": "PLUMBING",
            "suburb": "Hillside",
            "address": "14 Harrow Rd",
            "problem_description": "Leaking tap",
        },
    )
    job_id = job_res.json()["id"]

    await client.get(f"/jobs/{job_id}/matches", headers=auth_headers(buyer))
    await client.post(
        f"/jobs/{job_id}/book",
        headers=auth_headers(buyer),
        json={"worker_id": str(skilled_worker.id), "deposit_amount": str(Decimal("10.00"))},
    )
    await client.post(
        f"/jobs/{job_id}/quote",
        headers=auth_headers(skilled_worker),
        json={"labor_amount": "30.00", "materials_amount": "10.00"},
    )
    await client.post(
        f"/jobs/{job_id}/complete",
        headers=auth_headers(buyer),
        json={"what_was_done": "Replaced tap washer"},
    )

    review_res = await client.post(
        f"/jobs/{job_id}/review",
        headers=auth_headers(buyer),
        json={
            "rating": 5,
            "tags": ["ON_TIME", "QUALITY_WORK"],
            "comment": "Fast and tidy work",
        },
    )
    assert review_res.status_code == 201
    assert review_res.json()["rating"] == 5

    # Double-blind (ADR-011): the rating counts once the worker reviews too.
    hidden = await client.get("/workers/me/standing", headers=auth_headers(skilled_worker))
    assert hidden.json()["rating_count"] == 0
    worker_review = await client.post(
        f"/jobs/{job_id}/review",
        headers=auth_headers(skilled_worker),
        json={"rating": 4, "tags": ["PAID_ON_TIME"]},
    )
    assert worker_review.status_code == 201

    standing_res = await client.get("/workers/me/standing", headers=auth_headers(skilled_worker))
    assert standing_res.status_code == 200
    assert standing_res.json()["rating_count"] == 1
    assert Decimal(str(standing_res.json()["rating_average"])) == Decimal("5.00")
