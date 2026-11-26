import uuid

from sqlalchemy import update

from app.apps.jobs.domain.entities import JobStatusEnum
from app.apps.jobs.infrastructure.models import JobModel
from tests.conftest import auth_headers

PAYLOAD = {
    "trade": "PLUMBING",
    "suburb": "Nkulumane",
    "address": "12 Fife Street, Nkulumane",
    "landmark_narrative": "Blue gate opposite the clinic.",
    "latitude": "-20.2050",
    "longitude": "28.5300",
    "problem_description": "Leaking geyser, call me on 0771234567.",
    "budget_amount": "40.00",
    "needed_by": "TODAY",
    "pricing_mode": "FIXED",
}

ALLOWED_KEYS = {"job_id", "trade", "suburb", "needed_by", "pricing_mode", "is_open", "created_at"}


async def _create_job(client, buyer) -> str:
    response = await client.post("/jobs/request", json=PAYLOAD, headers=auth_headers(buyer))
    assert response.status_code == 201
    return str(response.json()["id"])


async def test_share_summary_is_public_and_minimal(client, buyer):
    job_id = await _create_job(client, buyer)

    response = await client.get(f"/jobs/{job_id}/share")

    assert response.status_code == 200
    body = response.json()
    assert set(body) == ALLOWED_KEYS
    assert body["job_id"] == job_id
    assert body["trade"] == "PLUMBING"
    assert body["suburb"] == "Nkulumane"
    assert body["needed_by"] == "TODAY"
    assert body["pricing_mode"] == "FIXED"
    assert body["is_open"] is True
    # Nothing that identifies the place, the buyer or the details leaks.
    text = response.text
    for secret in ("Fife", "Blue gate", "0771234567", "geyser", "40.00", str(buyer.id)):
        assert secret not in text


async def test_share_summary_marks_booked_job_as_filled(client, buyer, db_session):
    job_id = await _create_job(client, buyer)
    await db_session.execute(
        update(JobModel).where(JobModel.id == uuid.UUID(job_id)).values(status=JobStatusEnum.BOOKED)
    )
    await db_session.commit()

    response = await client.get(f"/jobs/{job_id}/share")

    assert response.status_code == 200
    assert response.json()["is_open"] is False


async def test_share_summary_hides_cancelled_job(client, buyer, db_session):
    job_id = await _create_job(client, buyer)
    await db_session.execute(
        update(JobModel)
        .where(JobModel.id == uuid.UUID(job_id))
        .values(status=JobStatusEnum.CANCELLED)
    )
    await db_session.commit()

    response = await client.get(f"/jobs/{job_id}/share")

    assert response.status_code == 404


async def test_share_summary_unknown_job_is_404(client):
    response = await client.get(f"/jobs/{uuid.uuid4()}/share")

    assert response.status_code == 404
