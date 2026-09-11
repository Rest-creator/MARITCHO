from tests.conftest import auth_headers


async def test_aggregator_can_create_crew(client, aggregator):
    response = await client.post(
        "/crews/me", json={"name": "Baba Moyo Crew"}, headers=auth_headers(aggregator)
    )

    assert response.status_code == 201
    body = response.json()
    assert body["lead_id"] == str(aggregator.id)
    assert body["name"] == "Baba Moyo Crew"
    assert body["member_ids"] == []


async def test_buyer_cannot_create_crew(client, buyer):
    response = await client.post(
        "/crews/me", json={"name": "Some Crew"}, headers=auth_headers(buyer)
    )

    assert response.status_code == 403


async def test_aggregator_cannot_create_second_crew(client, aggregator):
    await client.post("/crews/me", json={"name": "First"}, headers=auth_headers(aggregator))

    response = await client.post(
        "/crews/me", json={"name": "Second"}, headers=auth_headers(aggregator)
    )

    assert response.status_code == 409


async def test_get_own_crew_without_one_returns_404(client, aggregator):
    response = await client.get("/crews/me", headers=auth_headers(aggregator))

    assert response.status_code == 404


async def test_aggregator_can_add_worker_member(client, aggregator, worker):
    await client.post("/crews/me", json={"name": "Crew"}, headers=auth_headers(aggregator))

    response = await client.post(
        "/crews/me/members",
        json={"worker_id": str(worker.id)},
        headers=auth_headers(aggregator),
    )

    assert response.status_code == 201
    assert response.json()["member_ids"] == [str(worker.id)]


async def test_cannot_add_non_worker_as_member(client, aggregator, buyer):
    await client.post("/crews/me", json={"name": "Crew"}, headers=auth_headers(aggregator))

    response = await client.post(
        "/crews/me/members",
        json={"worker_id": str(buyer.id)},
        headers=auth_headers(aggregator),
    )

    assert response.status_code == 422


async def test_cannot_add_duplicate_member(client, aggregator, worker):
    await client.post("/crews/me", json={"name": "Crew"}, headers=auth_headers(aggregator))
    await client.post(
        "/crews/me/members",
        json={"worker_id": str(worker.id)},
        headers=auth_headers(aggregator),
    )

    response = await client.post(
        "/crews/me/members",
        json={"worker_id": str(worker.id)},
        headers=auth_headers(aggregator),
    )

    assert response.status_code == 409


async def test_aggregator_can_remove_member(client, aggregator, worker):
    await client.post("/crews/me", json={"name": "Crew"}, headers=auth_headers(aggregator))
    await client.post(
        "/crews/me/members",
        json={"worker_id": str(worker.id)},
        headers=auth_headers(aggregator),
    )

    response = await client.delete(
        f"/crews/me/members/{worker.id}", headers=auth_headers(aggregator)
    )

    assert response.status_code == 200
    assert response.json()["member_ids"] == []


async def test_remove_nonexistent_member_returns_404(client, aggregator, worker):
    await client.post("/crews/me", json={"name": "Crew"}, headers=auth_headers(aggregator))

    response = await client.delete(
        f"/crews/me/members/{worker.id}", headers=auth_headers(aggregator)
    )

    assert response.status_code == 404


async def test_each_aggregator_has_an_independent_crew(
    client, aggregator, other_aggregator, worker
):
    await client.post("/crews/me", json={"name": "Crew A"}, headers=auth_headers(aggregator))
    await client.post("/crews/me", json={"name": "Crew B"}, headers=auth_headers(other_aggregator))
    await client.post(
        "/crews/me/members",
        json={"worker_id": str(worker.id)},
        headers=auth_headers(aggregator),
    )

    crew_a = await client.get("/crews/me", headers=auth_headers(aggregator))
    crew_b = await client.get("/crews/me", headers=auth_headers(other_aggregator))

    assert crew_a.json()["name"] == "Crew A"
    assert crew_a.json()["member_ids"] == [str(worker.id)]
    assert crew_b.json()["name"] == "Crew B"
    assert crew_b.json()["member_ids"] == []
