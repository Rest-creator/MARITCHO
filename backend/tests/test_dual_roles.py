"""One account can hire (BUYER) and find work (WORKER), switching or both at once."""

from tests.conftest import auth_headers


async def _signup(client, phone: str, role: str) -> dict[str, str]:
    response = await client.post(
        "/auth/signup",
        json={"phone": phone, "password": "correct-horse", "name": "Rudo", "role": role},
    )
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


async def _me(client, headers: dict[str, str]) -> dict[str, object]:
    response = await client.get("/users/me", headers=headers)
    assert response.status_code == 200
    return dict(response.json())


async def test_switching_mode_keeps_both_sides(client):
    headers = await _signup(client, "+263771234801", "BUYER")
    assert (await _me(client, headers))["roles"] == ["BUYER"]

    to_worker = await client.patch("/users/me", json={"role": "WORKER"}, headers=headers)
    assert to_worker.status_code == 200
    assert to_worker.json()["role"] == "WORKER"
    assert to_worker.json()["roles"] == ["BUYER", "WORKER"]

    back = await client.patch("/users/me", json={"role": "BUYER"}, headers=headers)
    assert back.json()["role"] == "BUYER"
    assert back.json()["roles"] == ["BUYER", "WORKER"]


async def test_account_with_both_sides_uses_either_without_switching(client):
    headers = await _signup(client, "+263771234802", "WORKER")
    await client.patch("/users/me", json={"role": "BUYER"}, headers=headers)

    # In hiring mode, worker endpoints still work...
    skill = await client.post("/workers/me/skills", json={"trade": "PLUMBING"}, headers=headers)
    assert skill.status_code == 201, skill.text
    area = await client.post(
        "/workers/me/service-areas", json={"suburb": "Hillside"}, headers=headers
    )
    assert area.status_code == 201, area.text
    assert (await client.get("/jobs/open", headers=headers)).status_code == 200
    # ...and so do buyer endpoints.
    job = await client.post(
        "/jobs/request",
        headers=headers,
        json={
            "trade": "SOLAR",
            "suburb": "Hillside",
            "address": "14 Harrow Rd",
            "problem_description": "Inverter beeping and batteries not charging",
        },
    )
    assert job.status_code == 201, job.text
    # Worker settings save whatever mode the account is in.
    patched = await client.patch("/users/me", json={"travel_km": 30}, headers=headers)
    assert patched.json()["travel_km"] == 30


async def test_single_sided_accounts_are_still_kept_to_their_side(client, buyer):
    response = await client.post(
        "/workers/me/skills", json={"trade": "PLUMBING"}, headers=auth_headers(buyer)
    )
    assert response.status_code == 403


async def test_worker_in_hiring_mode_can_still_be_found_and_booked(client, buyer):
    dual = await _signup(client, "+263771234803", "WORKER")
    await client.post("/workers/me/skills", json={"trade": "PLUMBING"}, headers=dual)
    await client.post("/workers/me/service-areas", json={"suburb": "Hillside"}, headers=dual)
    dual_id = (await _me(client, dual))["id"]
    await client.patch("/users/me", json={"role": "BUYER"}, headers=dual)

    directory = await client.get(
        "/workers", params={"trade": "PLUMBING", "suburb": "Hillside"}, headers=auth_headers(buyer)
    )
    assert directory.status_code == 200
    assert dual_id in {item["worker_id"] for item in directory.json()}
    profile = await client.get(f"/workers/{dual_id}", headers=auth_headers(buyer))
    assert profile.status_code == 200

    job = await client.post(
        "/jobs/request",
        headers=auth_headers(buyer),
        json={
            "trade": "PLUMBING",
            "suburb": "Hillside",
            "address": "3 Main St",
            "problem_description": "Burst geyser pipe in the bathroom",
        },
    )
    job_id = job.json()["id"]
    await client.get(f"/jobs/{job_id}/matches", headers=auth_headers(buyer))
    booked = await client.post(
        f"/jobs/{job_id}/book",
        json={"worker_id": dual_id, "deposit_amount": "20.00"},
        headers=auth_headers(buyer),
    )
    assert booked.status_code == 200, booked.text
    assert booked.json()["worker_id"] == dual_id
