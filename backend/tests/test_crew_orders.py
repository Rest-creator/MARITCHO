from decimal import Decimal

from app.shared_kernel.enums import TradeEnum
from tests.conftest import auth_headers

ORDER_PAYLOAD = {
    "trade": "BUILDING",
    "suburb": "Nkulumane",
    "address": "Site 7, Nkulumane Industrial Area",
    "workers_needed": 2,
    "problem_description": "Need bricklayers for a 2-day wall job.",
}


async def _create_crew(
    client, aggregator, worker_factory, count, trade=TradeEnum.BUILDING, suburb="Nkulumane"
):
    await client.post(
        "/crews/me", json={"name": "Baba Moyo Crew"}, headers=auth_headers(aggregator)
    )
    workers = []
    for _ in range(count):
        w = await worker_factory(trade, suburb)
        add_response = await client.post(
            "/crews/me/members", json={"worker_id": str(w.id)}, headers=auth_headers(aggregator)
        )
        assert add_response.status_code == 201
        workers.append(w)

    crew_response = await client.get("/crews/me", headers=auth_headers(aggregator))
    return crew_response.json(), workers


async def _create_order(client, buyer, workers_needed=2):
    payload = {**ORDER_PAYLOAD, "workers_needed": workers_needed}
    response = await client.post("/crew-orders/request", json=payload, headers=auth_headers(buyer))
    assert response.status_code == 201
    return response.json()


async def _create_matched_order(client, buyer, workers_needed=2):
    order = await _create_order(client, buyer, workers_needed)
    await client.get(f"/crew-orders/{order['id']}/matches", headers=auth_headers(buyer))
    return order


async def test_crew_order_request_accepts_optional_geo_fields(client, buyer):
    payload = {
        **ORDER_PAYLOAD,
        "landmark_narrative": "Behind the industrial hardware depot.",
        "latitude": "-20.2050",
        "longitude": "28.5300",
    }

    response = await client.post(
        "/crew-orders/request", json=payload, headers=auth_headers(buyer)
    )

    assert response.status_code == 201
    body = response.json()
    assert body["landmark_narrative"] == payload["landmark_narrative"]
    assert body["latitude"] == "-20.205000"
    assert body["longitude"] == "28.530000"


async def test_crew_order_request_geo_fields_are_optional(client, buyer):
    order = await _create_order(client, buyer)

    assert order["landmark_narrative"] is None
    assert order["latitude"] is None
    assert order["longitude"] is None


async def test_crew_order_matches_returns_qualifying_crew(
    client, buyer, aggregator, worker_factory
):
    crew, _workers = await _create_crew(client, aggregator, worker_factory, count=3)
    order = await _create_order(client, buyer, workers_needed=2)

    response = await client.get(f"/crew-orders/{order['id']}/matches", headers=auth_headers(buyer))

    assert response.status_code == 200
    candidates = response.json()
    assert len(candidates) == 1
    assert candidates[0]["crew_id"] == crew["id"]
    assert candidates[0]["qualifying_members"] == 3
    assert candidates[0]["total_members"] == 3
    assert candidates[0]["reason"]


async def test_crew_order_excludes_crew_with_too_few_qualifying_members(
    client, buyer, aggregator, worker_factory
):
    await _create_crew(client, aggregator, worker_factory, count=1)
    order = await _create_order(client, buyer, workers_needed=2)

    response = await client.get(f"/crew-orders/{order['id']}/matches", headers=auth_headers(buyer))

    assert response.status_code == 200
    assert response.json() == []


async def test_crew_order_excludes_wrong_trade(client, buyer, aggregator, worker_factory):
    await _create_crew(client, aggregator, worker_factory, count=3, trade=TradeEnum.PLUMBING)
    order = await _create_order(client, buyer, workers_needed=2)

    response = await client.get(f"/crew-orders/{order['id']}/matches", headers=auth_headers(buyer))

    assert response.status_code == 200
    assert response.json() == []


async def test_crew_order_excludes_far_suburb(client, buyer, aggregator, worker_factory):
    # Hillside is ~10.7km from Nkulumane in the seeded suburb coordinates: FAR.
    await _create_crew(client, aggregator, worker_factory, count=3, suburb="Hillside")
    order = await _create_order(client, buyer, workers_needed=2)

    response = await client.get(f"/crew-orders/{order['id']}/matches", headers=auth_headers(buyer))

    assert response.status_code == 200
    assert response.json() == []


async def test_crew_order_quote_splits_into_labor_and_materials(
    client, buyer, aggregator, worker_factory
):
    crew, _workers = await _create_crew(client, aggregator, worker_factory, count=2)
    order = await _create_matched_order(client, buyer, workers_needed=2)
    await client.post(
        f"/crew-orders/{order['id']}/book",
        json={"crew_id": crew["id"], "deposit_amount": "500.00"},
        headers=auth_headers(buyer),
    )

    response = await client.post(
        f"/crew-orders/{order['id']}/quote",
        json={"labor_amount": "1500.00", "materials_amount": "600.00"},
        headers=auth_headers(aggregator),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["labor_amount"] == "1500.00"
    assert body["materials_amount"] == "600.00"
    assert body["quote_amount"] == "2100.00"


async def test_crew_order_full_lifecycle_and_ledger(client, buyer, aggregator, worker_factory):
    crew, _workers = await _create_crew(client, aggregator, worker_factory, count=2)
    order = await _create_matched_order(client, buyer, workers_needed=2)

    book_response = await client.post(
        f"/crew-orders/{order['id']}/book",
        json={"crew_id": crew["id"], "deposit_amount": "500.00"},
        headers=auth_headers(buyer),
    )
    assert book_response.status_code == 200
    assert book_response.json()["status"] == "BOOKED"
    assert book_response.json()["crew_id"] == crew["id"]

    quote_response = await client.post(
        f"/crew-orders/{order['id']}/quote",
        json={"labor_amount": "2000.00", "materials_amount": "0.00"},
        headers=auth_headers(aggregator),
    )
    assert quote_response.status_code == 200
    assert quote_response.json()["status"] == "IN_PROGRESS"

    complete_response = await client.post(
        f"/crew-orders/{order['id']}/complete",
        json={"what_was_done": "Wall built and inspected."},
        headers=auth_headers(buyer),
    )
    assert complete_response.status_code == 200
    assert complete_response.json()["status"] == "COMPLETED"
    assert complete_response.json()["completion_note"] == "Wall built and inspected."

    ledger_response = await client.get(
        f"/crew-orders/{order['id']}/ledger", headers=auth_headers(buyer)
    )
    by_type = {e["entry_type"]: Decimal(e["amount"]) for e in ledger_response.json()}
    assert by_type["DEPOSIT_HELD"] == Decimal("500.00")
    assert by_type["BALANCE_COMMITTED"] == Decimal("1500.00")
    assert by_type["RELEASED"] == Decimal("2000.00")


async def test_book_requires_matched_status(client, buyer, aggregator, worker_factory):
    crew, _workers = await _create_crew(client, aggregator, worker_factory, count=2)
    order = await _create_order(client, buyer, workers_needed=2)  # never matched

    response = await client.post(
        f"/crew-orders/{order['id']}/book",
        json={"crew_id": crew["id"], "deposit_amount": "500.00"},
        headers=auth_headers(buyer),
    )

    assert response.status_code == 409


async def test_book_rejects_non_owner_buyer(client, buyer, other_buyer, aggregator, worker_factory):
    crew, _workers = await _create_crew(client, aggregator, worker_factory, count=2)
    order = await _create_matched_order(client, buyer, workers_needed=2)

    response = await client.post(
        f"/crew-orders/{order['id']}/book",
        json={"crew_id": crew["id"], "deposit_amount": "500.00"},
        headers=auth_headers(other_buyer),
    )

    assert response.status_code == 403


async def test_book_rejects_already_busy_crew(client, buyer, aggregator, worker_factory):
    crew, _workers = await _create_crew(client, aggregator, worker_factory, count=2)
    order = await _create_matched_order(client, buyer, workers_needed=2)
    await client.post(
        f"/crew-orders/{order['id']}/book",
        json={"crew_id": crew["id"], "deposit_amount": "500.00"},
        headers=auth_headers(buyer),
    )

    other_order = await _create_matched_order(client, buyer, workers_needed=2)
    response = await client.post(
        f"/crew-orders/{other_order['id']}/book",
        json={"crew_id": crew["id"], "deposit_amount": "500.00"},
        headers=auth_headers(buyer),
    )

    assert response.status_code == 409


async def test_quote_requires_crew_lead(
    client, buyer, aggregator, other_aggregator, worker_factory
):
    crew, _workers = await _create_crew(client, aggregator, worker_factory, count=2)
    order = await _create_matched_order(client, buyer, workers_needed=2)
    await client.post(
        f"/crew-orders/{order['id']}/book",
        json={"crew_id": crew["id"], "deposit_amount": "500.00"},
        headers=auth_headers(buyer),
    )

    response = await client.post(
        f"/crew-orders/{order['id']}/quote",
        json={"labor_amount": "2000.00", "materials_amount": "0.00"},
        headers=auth_headers(other_aggregator),
    )

    assert response.status_code == 403


async def test_quote_requires_booked_status(client, buyer, aggregator, worker_factory):
    crew, _workers = await _create_crew(client, aggregator, worker_factory, count=2)
    order = await _create_matched_order(client, buyer, workers_needed=2)
    # never booked

    response = await client.post(
        f"/crew-orders/{order['id']}/quote",
        json={"labor_amount": "2000.00", "materials_amount": "0.00"},
        headers=auth_headers(aggregator),
    )

    assert response.status_code == 403


async def test_quote_rejects_amount_not_exceeding_deposit(
    client, buyer, aggregator, worker_factory
):
    crew, _workers = await _create_crew(client, aggregator, worker_factory, count=2)
    order = await _create_matched_order(client, buyer, workers_needed=2)
    await client.post(
        f"/crew-orders/{order['id']}/book",
        json={"crew_id": crew["id"], "deposit_amount": "500.00"},
        headers=auth_headers(buyer),
    )

    response = await client.post(
        f"/crew-orders/{order['id']}/quote",
        json={"labor_amount": "500.00", "materials_amount": "0.00"},
        headers=auth_headers(aggregator),
    )

    assert response.status_code == 422


async def test_complete_requires_buyer(client, buyer, aggregator, worker_factory):
    crew, _workers = await _create_crew(client, aggregator, worker_factory, count=2)
    order = await _create_matched_order(client, buyer, workers_needed=2)
    await client.post(
        f"/crew-orders/{order['id']}/book",
        json={"crew_id": crew["id"], "deposit_amount": "500.00"},
        headers=auth_headers(buyer),
    )
    await client.post(
        f"/crew-orders/{order['id']}/quote",
        json={"labor_amount": "2000.00", "materials_amount": "0.00"},
        headers=auth_headers(aggregator),
    )

    response = await client.post(
        f"/crew-orders/{order['id']}/complete",
        json={"what_was_done": "Done."},
        headers=auth_headers(aggregator),
    )

    assert response.status_code == 403


async def test_complete_requires_in_progress_status(client, buyer, aggregator, worker_factory):
    crew, _workers = await _create_crew(client, aggregator, worker_factory, count=2)
    order = await _create_matched_order(client, buyer, workers_needed=2)
    await client.post(
        f"/crew-orders/{order['id']}/book",
        json={"crew_id": crew["id"], "deposit_amount": "500.00"},
        headers=auth_headers(buyer),
    )
    # never quoted, still BOOKED

    response = await client.post(
        f"/crew-orders/{order['id']}/complete",
        json={"what_was_done": "Done."},
        headers=auth_headers(buyer),
    )

    assert response.status_code == 409


async def test_ledger_hidden_from_unrelated_buyer(
    client, buyer, other_buyer, aggregator, worker_factory
):
    crew, _workers = await _create_crew(client, aggregator, worker_factory, count=2)
    order = await _create_matched_order(client, buyer, workers_needed=2)
    await client.post(
        f"/crew-orders/{order['id']}/book",
        json={"crew_id": crew["id"], "deposit_amount": "500.00"},
        headers=auth_headers(buyer),
    )

    response = await client.get(
        f"/crew-orders/{order['id']}/ledger", headers=auth_headers(other_buyer)
    )

    assert response.status_code == 403


async def test_crew_lead_can_view_order_once_booked(client, buyer, aggregator, worker_factory):
    crew, _workers = await _create_crew(client, aggregator, worker_factory, count=2)
    order = await _create_matched_order(client, buyer, workers_needed=2)
    await client.post(
        f"/crew-orders/{order['id']}/book",
        json={"crew_id": crew["id"], "deposit_amount": "500.00"},
        headers=auth_headers(buyer),
    )

    response = await client.get(f"/crew-orders/{order['id']}", headers=auth_headers(aggregator))

    assert response.status_code == 200
