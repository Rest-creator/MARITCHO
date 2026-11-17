from app.shared_kernel.enums import TradeEnum
from tests.conftest import auth_headers


async def test_worker_can_register_skill(client, worker):
    response = await client.post(
        "/workers/me/skills", json={"trade": "PLUMBING"}, headers=auth_headers(worker)
    )

    assert response.status_code == 201
    body = response.json()
    assert body["trade"] == "PLUMBING"
    assert body["worker_id"] == str(worker.id)


async def test_buyer_cannot_register_skill(client, buyer):
    response = await client.post(
        "/workers/me/skills", json={"trade": "PLUMBING"}, headers=auth_headers(buyer)
    )

    assert response.status_code == 403


async def test_worker_cannot_register_duplicate_skill(client, worker):
    await client.post(
        "/workers/me/skills", json={"trade": "PLUMBING"}, headers=auth_headers(worker)
    )

    response = await client.post(
        "/workers/me/skills", json={"trade": "PLUMBING"}, headers=auth_headers(worker)
    )

    assert response.status_code == 409


async def test_worker_can_list_own_skills(client, worker):
    await client.post(
        "/workers/me/skills", json={"trade": "PLUMBING"}, headers=auth_headers(worker)
    )
    await client.post(
        "/workers/me/skills", json={"trade": "ELECTRICAL"}, headers=auth_headers(worker)
    )

    response = await client.get("/workers/me/skills", headers=auth_headers(worker))

    assert response.status_code == 200
    trades = {s["trade"] for s in response.json()}
    assert trades == {"PLUMBING", "ELECTRICAL"}


async def test_worker_can_register_service_area(client, worker):
    response = await client.post(
        "/workers/me/service-areas",
        json={"suburb": "Nkulumane", "travel_means": "WALKING"},
        headers=auth_headers(worker),
    )

    assert response.status_code == 201
    body = response.json()
    assert body["suburb"] == "Nkulumane"
    assert body["travel_means"] == "WALKING"


async def test_worker_cannot_register_unknown_suburb(client, worker):
    response = await client.post(
        "/workers/me/service-areas",
        json={"suburb": "Atlantis"},
        headers=auth_headers(worker),
    )

    assert response.status_code == 422


async def test_worker_cannot_register_duplicate_service_area(client, worker):
    await client.post(
        "/workers/me/service-areas",
        json={"suburb": "Nkulumane"},
        headers=auth_headers(worker),
    )

    response = await client.post(
        "/workers/me/service-areas",
        json={"suburb": "Nkulumane"},
        headers=auth_headers(worker),
    )

    assert response.status_code == 409


async def test_worker_can_list_own_service_areas(client, worker):
    await client.post(
        "/workers/me/service-areas", json={"suburb": "Nkulumane"}, headers=auth_headers(worker)
    )
    await client.post(
        "/workers/me/service-areas", json={"suburb": "Hillside"}, headers=auth_headers(worker)
    )

    response = await client.get("/workers/me/service-areas", headers=auth_headers(worker))

    assert response.status_code == 200
    suburbs = {s["suburb"] for s in response.json()}
    assert suburbs == {"Nkulumane", "Hillside"}


async def test_worker_standing_defaults_before_any_registration(client, worker):
    response = await client.get("/workers/me/standing", headers=auth_headers(worker))

    assert response.status_code == 200
    body = response.json()
    assert body["grade"] == "REGISTERED"
    assert body["jobs_completed"] == 0
    assert body["is_frozen"] is False


async def test_registering_skill_creates_a_standing_row(client, worker):
    await client.post(
        "/workers/me/skills", json={"trade": "PLUMBING"}, headers=auth_headers(worker)
    )

    response = await client.get("/workers/me/standing", headers=auth_headers(worker))

    assert response.status_code == 200
    assert response.json()["worker_id"] == str(worker.id)


async def test_buyer_can_browse_nearby_workers_and_view_public_profile(client, buyer, worker):
    await client.post(
        "/workers/me/skills",
        json={"trade": "PLUMBING", "proof_url": "/media/work-1.jpg"},
        headers=auth_headers(worker),
    )
    await client.post(
        "/workers/me/service-areas",
        json={"suburb": "Hillside", "travel_means": "COMBI"},
        headers=auth_headers(worker),
    )

    directory = await client.get(
        "/workers",
        params={"suburb": "Hillside", "trade": "PLUMBING"},
        headers=auth_headers(buyer),
    )
    assert directory.status_code == 200
    items = directory.json()
    assert len(items) == 1
    assert items[0]["worker_id"] == str(worker.id)
    assert items[0]["distance_band"] == "SAME_SUBURB"
    assert items[0]["trades"] == ["PLUMBING"]

    profile = await client.get(
        f"/workers/{worker.id}",
        params={"suburb": "Hillside"},
        headers=auth_headers(buyer),
    )
    assert profile.status_code == 200
    body = profile.json()
    assert body["worker_id"] == str(worker.id)
    assert body["service_areas"] == ["Hillside"]
    assert body["proof_urls"] == ["/media/work-1.jpg"]

    # Semantic vector query ("pombi yemvura" -> PLUMBING) finds the plumber
    semantic = await client.get(
        "/workers",
        params={"suburb": "Hillside", "q": "pombi yemvura leaking geyser"},
        headers=auth_headers(buyer),
    )
    assert semantic.status_code == 200
    sem_items = semantic.json()
    assert len(sem_items) == 1
    assert sem_items[0]["worker_id"] == str(worker.id)
    assert sem_items[0]["similarity_score"] is not None


async def test_worker_cannot_browse_the_employer_directory(client, worker, worker_factory):
    """The worker directory is an employer-facing feature (regression:
    both routes used bare get_current_user, letting any authenticated
    worker browse the full directory and other workers' profiles)."""
    other_worker = await worker_factory(TradeEnum.PLUMBING, "Hillside")

    directory = await client.get(
        "/workers",
        params={"suburb": "Hillside"},
        headers=auth_headers(worker),
    )
    assert directory.status_code == 403

    profile = await client.get(
        f"/workers/{other_worker.id}",
        params={"suburb": "Hillside"},
        headers=auth_headers(worker),
    )
    assert profile.status_code == 403


