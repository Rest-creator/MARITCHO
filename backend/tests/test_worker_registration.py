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
