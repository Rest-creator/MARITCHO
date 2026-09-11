from tests.conftest import auth_headers

VALID_PAYLOAD = {
    "trade": "PLUMBING",
    "suburb": "Nkulumane",
    "address": "12 Fife Street, Nkulumane",
    "problem_description": "Leaking geyser in the bathroom, water on the floor.",
}


async def test_buyer_can_create_job_request(client, buyer):
    response = await client.post(
        "/jobs/request", json=VALID_PAYLOAD, headers=auth_headers(buyer)
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "REQUESTED"
    assert body["trade"] == VALID_PAYLOAD["trade"]
    assert body["suburb"] == VALID_PAYLOAD["suburb"]
    assert body["address"] == VALID_PAYLOAD["address"]
    assert body["problem_description"] == VALID_PAYLOAD["problem_description"]
    assert body["buyer_id"] == str(buyer.id)
    assert body["worker_id"] is None


async def test_buyer_id_cannot_be_spoofed_via_payload(client, buyer, other_buyer):
    payload = {**VALID_PAYLOAD, "buyer_id": str(other_buyer.id)}

    response = await client.post("/jobs/request", json=payload, headers=auth_headers(buyer))

    assert response.status_code == 201
    assert response.json()["buyer_id"] == str(buyer.id)


async def test_worker_cannot_create_job_request(client, worker):
    response = await client.post(
        "/jobs/request", json=VALID_PAYLOAD, headers=auth_headers(worker)
    )

    assert response.status_code == 403


async def test_unauthenticated_cannot_create_job_request(client):
    response = await client.post("/jobs/request", json=VALID_PAYLOAD)

    assert response.status_code == 401


async def test_job_request_requires_suburb_and_description(client, buyer):
    response = await client.post("/jobs/request", json={}, headers=auth_headers(buyer))

    assert response.status_code == 422


async def test_job_request_sanitizes_html_in_description(client, buyer):
    payload = {
        "trade": "PLUMBING",
        "suburb": "Nkulumane",
        "address": "12 Fife Street, Nkulumane",
        "problem_description": "<script>alert(1)</script>Leaking pipe under the sink",
    }

    response = await client.post("/jobs/request", json=payload, headers=auth_headers(buyer))

    assert response.status_code == 201
    description = response.json()["problem_description"]
    assert "<" not in description and ">" not in description
    assert "Leaking pipe under the sink" in description


async def test_job_request_rejects_blank_description_after_sanitization(client, buyer):
    payload = {
        "trade": "PLUMBING",
        "suburb": "Nkulumane",
        "address": "12 Fife Street, Nkulumane",
        "problem_description": "   <b></b>   ",
    }

    response = await client.post("/jobs/request", json=payload, headers=auth_headers(buyer))

    assert response.status_code == 422


async def test_job_request_rejects_unknown_suburb(client, buyer):
    payload = {**VALID_PAYLOAD, "suburb": "Atlantis"}

    response = await client.post("/jobs/request", json=payload, headers=auth_headers(buyer))

    assert response.status_code == 422


async def test_buyer_can_fetch_own_job(client, buyer):
    create_response = await client.post(
        "/jobs/request", json=VALID_PAYLOAD, headers=auth_headers(buyer)
    )
    job_id = create_response.json()["id"]

    response = await client.get(f"/jobs/{job_id}", headers=auth_headers(buyer))

    assert response.status_code == 200
    assert response.json()["id"] == job_id


async def test_other_buyer_cannot_fetch_foreign_job(client, buyer, other_buyer):
    create_response = await client.post(
        "/jobs/request", json=VALID_PAYLOAD, headers=auth_headers(buyer)
    )
    job_id = create_response.json()["id"]

    response = await client.get(f"/jobs/{job_id}", headers=auth_headers(other_buyer))

    assert response.status_code == 403


async def test_ops_can_fetch_any_job(client, buyer, ops_user):
    create_response = await client.post(
        "/jobs/request", json=VALID_PAYLOAD, headers=auth_headers(buyer)
    )
    job_id = create_response.json()["id"]

    response = await client.get(f"/jobs/{job_id}", headers=auth_headers(ops_user))

    assert response.status_code == 200


async def test_fetch_nonexistent_job_returns_404(client, buyer):
    missing_id = "00000000-0000-0000-0000-000000000000"

    response = await client.get(f"/jobs/{missing_id}", headers=auth_headers(buyer))

    assert response.status_code == 404
