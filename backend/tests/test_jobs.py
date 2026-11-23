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


async def test_buyer_can_create_job_request_with_geo_fields(client, buyer):
    payload = {
        **VALID_PAYLOAD,
        "landmark_narrative": "Blue gate opposite the municipal clinic.",
        "latitude": "-20.2050",
        "longitude": "28.5300",
    }

    response = await client.post("/jobs/request", json=payload, headers=auth_headers(buyer))

    assert response.status_code == 201
    body = response.json()
    assert body["landmark_narrative"] == payload["landmark_narrative"]
    assert body["latitude"] == "-20.205000"
    assert body["longitude"] == "28.530000"


async def test_job_request_geo_fields_are_optional(client, buyer):
    response = await client.post(
        "/jobs/request", json=VALID_PAYLOAD, headers=auth_headers(buyer)
    )

    assert response.status_code == 201
    body = response.json()
    assert body["landmark_narrative"] is None
    assert body["latitude"] is None
    assert body["longitude"] is None


async def test_job_request_rejects_out_of_range_latitude(client, buyer):
    payload = {**VALID_PAYLOAD, "latitude": "95.0"}

    response = await client.post("/jobs/request", json=payload, headers=auth_headers(buyer))

    assert response.status_code == 422


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


async def test_buyer_can_create_job_with_pricing_modes(client, buyer):
    fixed = await client.post(
        "/jobs/request",
        json={**VALID_PAYLOAD, "pricing_mode": "FIXED", "budget_amount": "45.00"},
        headers=auth_headers(buyer),
    )
    assert fixed.status_code == 201
    assert fixed.json()["pricing_mode"] == "FIXED"
    assert fixed.json()["budget_amount"] == "45.00"

    after_visit = await client.post(
        "/jobs/request",
        json={**VALID_PAYLOAD, "pricing_mode": "AFTER_VISIT"},
        headers=auth_headers(buyer),
    )
    assert after_visit.status_code == 201
    assert after_visit.json()["pricing_mode"] == "AFTER_VISIT"
    assert after_visit.json()["budget_amount"] is None


async def test_fixed_pricing_mode_requires_budget_amount(client, buyer):
    response = await client.post(
        "/jobs/request",
        json={**VALID_PAYLOAD, "pricing_mode": "FIXED"},
        headers=auth_headers(buyer),
    )
    assert response.status_code == 422


async def test_buyer_can_edit_open_job_posting(client, buyer, other_buyer):
    created = await client.post(
        "/jobs/request",
        json={**VALID_PAYLOAD, "pricing_mode": "FIXED", "budget_amount": "30.00"},
        headers=auth_headers(buyer),
    )
    assert created.status_code == 201
    job_id = created.json()["id"]

    # Another buyer cannot edit this job
    forbidden = await client.patch(
        f"/jobs/{job_id}",
        json={"problem_description": "Unauthorized edit"},
        headers=auth_headers(other_buyer),
    )
    assert forbidden.status_code == 403

    # Owner can edit description, pricing mode, and budget
    updated = await client.patch(
        f"/jobs/{job_id}",
        json={
            "problem_description": "Updated: burst pipe in kitchen",
            "pricing_mode": "NEGOTIABLE",
            "budget_amount": "50.00",
        },
        headers=auth_headers(buyer),
    )
    assert updated.status_code == 200
    body = updated.json()
    assert body["problem_description"] == "Updated: burst pipe in kitchen"
    assert body["pricing_mode"] == "NEGOTIABLE"
    assert body["budget_amount"] == "50.00"

    # Switching to AFTER_VISIT clears budget_amount when not supplied
    after_visit = await client.patch(
        f"/jobs/{job_id}",
        json={"pricing_mode": "AFTER_VISIT"},
        headers=auth_headers(buyer),
    )
    assert after_visit.status_code == 200
    assert after_visit.json()["pricing_mode"] == "AFTER_VISIT"
    assert after_visit.json()["budget_amount"] is None
