import uuid
from decimal import Decimal

from app.models import Job, TradeEnum
from tests.conftest import auth_headers

JOB_PAYLOAD = {
    "trade": "PLUMBING",
    "suburb": "Nkulumane",
    "address": "12 Fife Street, Nkulumane",
    "problem_description": "Leaking geyser in the bathroom, water on the floor.",
}


async def _create_matched_job(client, buyer, worker_factory):
    worker = await worker_factory(TradeEnum.PLUMBING, "Nkulumane")

    create_response = await client.post(
        "/jobs/request", json=JOB_PAYLOAD, headers=auth_headers(buyer)
    )
    job = create_response.json()

    await client.get(f"/jobs/{job['id']}/matches", headers=auth_headers(buyer))

    return job, worker


async def _book(client, buyer, job, worker, deposit_amount="50.00"):
    return await client.post(
        f"/jobs/{job['id']}/book",
        json={"worker_id": str(worker.id), "deposit_amount": deposit_amount},
        headers=auth_headers(buyer),
    )


async def test_full_lifecycle_creates_correct_ledger_and_record(
    client, buyer, worker_factory
):
    job, worker = await _create_matched_job(client, buyer, worker_factory)

    book_response = await _book(client, buyer, job, worker, deposit_amount="50.00")
    assert book_response.status_code == 200
    booked = book_response.json()
    assert booked["status"] == "BOOKED"
    assert booked["worker_id"] == str(worker.id)
    assert booked["address"] == JOB_PAYLOAD["address"]

    quote_response = await client.post(
        f"/jobs/{job['id']}/quote",
        json={"quote_amount": "200.00"},
        headers=auth_headers(worker),
    )
    assert quote_response.status_code == 200
    quoted = quote_response.json()
    assert quoted["status"] == "IN_PROGRESS"
    assert quoted["quote_amount"] == "200.00"

    complete_response = await client.post(
        f"/jobs/{job['id']}/complete",
        json={
            "what_was_done": "Replaced the geyser element and tested the pressure valve.",
            "client_words": "Quick and tidy work.",
            "before_photo_url": "https://example.com/before.jpg",
            "after_photo_url": "https://example.com/after.jpg",
        },
        headers=auth_headers(buyer),
    )
    assert complete_response.status_code == 200
    assert complete_response.json()["status"] == "COMPLETED"

    ledger_response = await client.get(
        f"/jobs/{job['id']}/ledger", headers=auth_headers(buyer)
    )
    entries = ledger_response.json()
    by_type = {e["entry_type"]: Decimal(e["amount"]) for e in entries}
    assert by_type["DEPOSIT_HELD"] == Decimal("50.00")
    assert by_type["BALANCE_COMMITTED"] == Decimal("150.00")
    assert by_type["RELEASED"] == Decimal("200.00")

    record_response = await client.get(
        f"/jobs/{job['id']}/record", headers=auth_headers(buyer)
    )
    record = record_response.json()
    assert record["worker_id"] == str(worker.id)
    assert "Replaced the geyser element" in record["what_was_done"]
    assert record["client_words"] == "Quick and tidy work."


async def test_book_requires_matched_status(client, buyer, worker_factory):
    worker = await worker_factory(TradeEnum.PLUMBING, "Nkulumane")
    create_response = await client.post(
        "/jobs/request", json=JOB_PAYLOAD, headers=auth_headers(buyer)
    )
    job = create_response.json()  # still REQUESTED, matches never called

    response = await _book(client, buyer, job, worker)

    assert response.status_code == 409


async def test_book_rejects_non_owner_buyer(client, buyer, other_buyer, worker_factory):
    job, worker = await _create_matched_job(client, buyer, worker_factory)

    response = await _book(client, other_buyer, job, worker)

    assert response.status_code == 403


async def test_book_rejects_unknown_worker_id(client, buyer, worker_factory):
    job, _worker = await _create_matched_job(client, buyer, worker_factory)

    response = await client.post(
        f"/jobs/{job['id']}/book",
        json={
            "worker_id": "00000000-0000-0000-0000-000000000000",
            "deposit_amount": "50.00",
        },
        headers=auth_headers(buyer),
    )

    assert response.status_code == 422


async def test_book_rejects_worker_without_matching_skill(
    client, buyer, worker_factory
):
    job, _matched_worker = await _create_matched_job(client, buyer, worker_factory)
    wrong_skill_worker = await worker_factory(TradeEnum.ELECTRICAL, "Nkulumane")

    response = await _book(client, buyer, job, wrong_skill_worker)

    assert response.status_code == 422


async def test_book_rejects_already_busy_worker(client, buyer, worker_factory):
    job, worker = await _create_matched_job(client, buyer, worker_factory)
    await _book(client, buyer, job, worker)

    other_job_response = await client.post(
        "/jobs/request", json=JOB_PAYLOAD, headers=auth_headers(buyer)
    )
    other_job = other_job_response.json()
    await client.get(f"/jobs/{other_job['id']}/matches", headers=auth_headers(buyer))

    response = await _book(client, buyer, other_job, worker)

    assert response.status_code == 409


async def test_quote_requires_assigned_worker(client, buyer, worker_factory):
    job, worker = await _create_matched_job(client, buyer, worker_factory)
    await _book(client, buyer, job, worker)
    impostor = await worker_factory(TradeEnum.PLUMBING, "Njube")

    response = await client.post(
        f"/jobs/{job['id']}/quote",
        json={"quote_amount": "200.00"},
        headers=auth_headers(impostor),
    )

    assert response.status_code == 403


async def test_quote_rejected_before_booking(client, buyer, worker_factory):
    job, worker = await _create_matched_job(client, buyer, worker_factory)
    # not booked yet: job.worker_id is still unset, so this candidate isn't
    # the assigned worker regardless of job status.

    response = await client.post(
        f"/jobs/{job['id']}/quote",
        json={"quote_amount": "200.00"},
        headers=auth_headers(worker),
    )

    assert response.status_code == 403


async def test_quote_requires_booked_status(client, buyer, worker_factory, db_session):
    job, worker = await _create_matched_job(client, buyer, worker_factory)
    # Assign the worker directly without going through /book, so status
    # stays MATCHED instead of BOOKED, to isolate the status gate itself.
    db_job = await db_session.get(Job, uuid.UUID(job["id"]))
    db_job.worker_id = worker.id
    await db_session.commit()

    response = await client.post(
        f"/jobs/{job['id']}/quote",
        json={"quote_amount": "200.00"},
        headers=auth_headers(worker),
    )

    assert response.status_code == 409


async def test_quote_rejects_amount_not_exceeding_deposit(client, buyer, worker_factory):
    job, worker = await _create_matched_job(client, buyer, worker_factory)
    await _book(client, buyer, job, worker, deposit_amount="50.00")

    response = await client.post(
        f"/jobs/{job['id']}/quote",
        json={"quote_amount": "50.00"},
        headers=auth_headers(worker),
    )

    assert response.status_code == 422


async def test_complete_requires_buyer(client, buyer, worker_factory):
    job, worker = await _create_matched_job(client, buyer, worker_factory)
    await _book(client, buyer, job, worker)
    await client.post(
        f"/jobs/{job['id']}/quote",
        json={"quote_amount": "200.00"},
        headers=auth_headers(worker),
    )

    response = await client.post(
        f"/jobs/{job['id']}/complete",
        json={"what_was_done": "Done."},
        headers=auth_headers(worker),
    )

    assert response.status_code == 403


async def test_complete_requires_in_progress_status(client, buyer, worker_factory):
    job, worker = await _create_matched_job(client, buyer, worker_factory)
    await _book(client, buyer, job, worker)
    # quote never submitted, still BOOKED

    response = await client.post(
        f"/jobs/{job['id']}/complete",
        json={"what_was_done": "Done."},
        headers=auth_headers(buyer),
    )

    assert response.status_code == 409


async def test_ledger_hidden_from_unrelated_buyer(client, buyer, other_buyer, worker_factory):
    job, worker = await _create_matched_job(client, buyer, worker_factory)
    await _book(client, buyer, job, worker)

    response = await client.get(
        f"/jobs/{job['id']}/ledger", headers=auth_headers(other_buyer)
    )

    assert response.status_code == 403


async def test_record_returns_404_before_completion(client, buyer, worker_factory):
    job, worker = await _create_matched_job(client, buyer, worker_factory)
    await _book(client, buyer, job, worker)

    response = await client.get(
        f"/jobs/{job['id']}/record", headers=auth_headers(buyer)
    )

    assert response.status_code == 404
