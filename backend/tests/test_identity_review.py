"""ADR-010: identity documents are private uploads, and badges follow an OPS review."""

import uuid
from datetime import timedelta
from pathlib import Path

import pytest

from app.apps.media import router as media_router
from app.apps.workers.domain.identity import (
    hash_id_number,
    media_id_from_url,
    normalize_zim_id_number,
)
from app.shared_kernel.clock import utcnow
from app.shared_kernel.enums import TradeEnum
from tests.conftest import auth_headers

JPEG_BYTES = b"\xff\xd8\xff\xe0" + b"\x00" * 64 + b"\xff\xd9"
ID_NUMBER = "08-2047823 Q 29"


@pytest.fixture(autouse=True)
def media_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = tmp_path / "media"
    monkeypatch.setattr(media_router, "MEDIA_ROOT", root)
    return root


async def _upload(client, person, key: str) -> str:
    response = await client.post(
        "/media/upload",
        headers={**auth_headers(person), "Idempotency-Key": key},
        files={"file": ("doc.jpg", JPEG_BYTES, "image/jpeg")},
    )
    assert response.status_code == 201
    return str(response.json()["url"])


async def _submit_id(client, worker):
    url = await _upload(client, worker, f"id-{worker.id}")
    response = await client.post(
        "/workers/me/vetting/id-photo",
        json={"id_photo_url": url},
        headers=auth_headers(worker),
    )
    assert response.status_code == 200
    return response.json()


async def _submit_clearance(client, worker):
    url = await _upload(client, worker, f"pc-{worker.id}")
    response = await client.post(
        "/workers/me/vetting/police-clearance",
        json={"police_clearance_url": url},
        headers=auth_headers(worker),
    )
    assert response.status_code == 200
    return response.json()


async def _approve_id(client, ops_user, worker, id_number: str = ID_NUMBER):
    return await client.post(
        f"/ops/vetting/{worker.id}/id",
        json={"decision": "APPROVE", "verified_name": "Tendai Moyo", "id_number": id_number},
        headers=auth_headers(ops_user),
    )


async def _profile(client, viewer, worker):
    response = await client.get(f"/workers/{worker.id}", headers=auth_headers(viewer))
    assert response.status_code == 200
    return response.json()


# ---- pure rules -------------------------------------------------------------


def test_zim_id_numbers_are_normalized_or_rejected():
    assert normalize_zim_id_number("08-2047823 q 29") == "082047823Q29"
    assert normalize_zim_id_number("63-123456 A 75") == "63123456A75"
    assert normalize_zim_id_number("12345") is None
    assert normalize_zim_id_number("08-2047823-29") is None


def test_id_number_hash_is_keyed_and_hides_the_number():
    first = hash_id_number("082047823Q29", b"key-a")
    assert first == hash_id_number("082047823Q29", b"key-a")
    assert first != hash_id_number("082047823Q29", b"key-b")
    assert "2047823" not in first


def test_only_media_paths_are_accepted_as_document_urls():
    media_id = uuid.uuid4()
    assert media_id_from_url(f"/media/{media_id}") == media_id
    assert media_id_from_url("https://example.com/id.jpg") is None
    assert media_id_from_url(f"/media/{media_id}/../x") is None


# ---- submitting -------------------------------------------------------------


async def test_submitting_an_id_waits_for_review_and_grants_nothing(client, worker_factory):
    worker = await worker_factory(TradeEnum.PLUMBING, "Nkulumane")

    body = await _submit_id(client, worker)

    assert body["id_status"] == "PENDING"
    assert body["grade"] == "REGISTERED"
    assert body["id_photo_url"].startswith("/media/")


async def test_an_outside_link_is_not_accepted_as_an_id(client, worker_factory):
    worker = await worker_factory(TradeEnum.PLUMBING, "Nkulumane")

    response = await client.post(
        "/workers/me/vetting/id-photo",
        json={"id_photo_url": "https://example.com/id.jpg"},
        headers=auth_headers(worker),
    )

    assert response.status_code == 422


async def test_someone_elses_upload_is_not_accepted(client, worker_factory, buyer):
    worker = await worker_factory(TradeEnum.PLUMBING, "Nkulumane")
    url = await _upload(client, buyer, "buyers-photo")

    response = await client.post(
        "/workers/me/vetting/police-clearance",
        json={"police_clearance_url": url},
        headers=auth_headers(worker),
    )

    assert response.status_code == 422


async def test_document_photos_stay_private(client, worker_factory, buyer, ops_user):
    worker = await worker_factory(TradeEnum.PLUMBING, "Nkulumane")
    body = await _submit_id(client, worker)
    url = body["id_photo_url"]

    assert (await client.get(url, headers=auth_headers(buyer))).status_code == 404
    assert (await client.get(url, headers=auth_headers(worker))).status_code == 200
    assert (await client.get(url, headers=auth_headers(ops_user))).status_code == 200
    profile = await _profile(client, buyer, worker)
    assert url not in str(profile)


# ---- OPS review: ID ---------------------------------------------------------


async def test_ops_queue_lists_waiting_documents(client, worker_factory, ops_user):
    worker = await worker_factory(TradeEnum.PLUMBING, "Nkulumane")
    await _submit_id(client, worker)
    await _submit_clearance(client, worker)

    response = await client.get("/ops/vetting/pending", headers=auth_headers(ops_user))

    assert response.status_code == 200
    documents = {(row["worker_id"], row["document"]) for row in response.json()}
    assert documents == {(str(worker.id), "ID"), (str(worker.id), "POLICE_CLEARANCE")}


async def test_only_ops_can_review(client, worker_factory, buyer):
    worker = await worker_factory(TradeEnum.PLUMBING, "Nkulumane")
    await _submit_id(client, worker)

    assert (
        await client.get("/ops/vetting/pending", headers=auth_headers(worker))
    ).status_code == 403
    assert (await _approve_id(client, buyer, worker)).status_code == 403


async def test_approving_an_id_makes_the_worker_identified(client, worker_factory, ops_user):
    worker = await worker_factory(TradeEnum.PLUMBING, "Nkulumane")
    await _submit_id(client, worker)

    response = await _approve_id(client, ops_user, worker)

    assert response.status_code == 200
    body = response.json()
    assert body["id_status"] == "VERIFIED"
    assert body["id_verified_name"] == "Tendai Moyo"
    assert body["grade"] == "IDENTIFIED"
    assert "2047823" not in str(body)
    queue = await client.get("/ops/vetting/pending", headers=auth_headers(ops_user))
    assert queue.json() == []


async def test_approved_id_plus_reference_promotes_to_apprentice(client, worker_factory, ops_user):
    worker = await worker_factory(TradeEnum.PLUMBING, "Nkulumane")
    await _submit_id(client, worker)
    await _approve_id(client, ops_user, worker)

    await client.post(
        "/workers/me/references",
        json={"name": "Mai Ncube", "phone": "+263771234567"},
        headers=auth_headers(worker),
    )

    vetting = await client.get("/workers/me/vetting", headers=auth_headers(worker))
    assert vetting.json()["grade"] == "APPRENTICE"


async def test_rejecting_an_id_tells_the_worker_why(client, worker_factory, ops_user):
    worker = await worker_factory(TradeEnum.PLUMBING, "Nkulumane")
    await _submit_id(client, worker)

    response = await client.post(
        f"/ops/vetting/{worker.id}/id",
        json={"decision": "REJECT", "rejection_reason": "The photo is blurry"},
        headers=auth_headers(ops_user),
    )

    assert response.status_code == 200
    vetting = (await client.get("/workers/me/vetting", headers=auth_headers(worker))).json()
    assert vetting["id_status"] == "REJECTED"
    assert vetting["id_rejection_reason"] == "The photo is blurry"
    assert vetting["grade"] == "REGISTERED"


async def test_rejecting_needs_a_reason_and_approving_needs_a_valid_number(
    client, worker_factory, ops_user
):
    worker = await worker_factory(TradeEnum.PLUMBING, "Nkulumane")
    await _submit_id(client, worker)

    no_reason = await client.post(
        f"/ops/vetting/{worker.id}/id",
        json={"decision": "REJECT"},
        headers=auth_headers(ops_user),
    )
    bad_number = await _approve_id(client, ops_user, worker, id_number="12345")

    assert no_reason.status_code == 422
    assert bad_number.status_code == 422


async def test_one_national_id_verifies_only_one_account(client, worker_factory, ops_user):
    first = await worker_factory(TradeEnum.PLUMBING, "Nkulumane")
    second = await worker_factory(TradeEnum.PLUMBING, "Nkulumane")
    await _submit_id(client, first)
    await _submit_id(client, second)
    assert (await _approve_id(client, ops_user, first)).status_code == 200

    response = await _approve_id(client, ops_user, second, id_number="082047823q29")

    assert response.status_code == 409


async def test_replacing_an_approved_id_needs_a_new_review(client, worker_factory, ops_user):
    worker = await worker_factory(TradeEnum.PLUMBING, "Nkulumane")
    await _submit_id(client, worker)
    await _approve_id(client, ops_user, worker)

    url = await _upload(client, worker, "id-replacement")
    response = await client.post(
        "/workers/me/vetting/id-photo",
        json={"id_photo_url": url},
        headers=auth_headers(worker),
    )

    assert response.json()["id_status"] == "PENDING"
    assert response.json()["grade"] == "REGISTERED"


async def test_reviewing_a_worker_without_an_id_is_404(client, worker_factory, ops_user):
    worker = await worker_factory(TradeEnum.PLUMBING, "Nkulumane")

    assert (await _approve_id(client, ops_user, worker)).status_code == 404


# ---- OPS review: police clearance ------------------------------------------


async def test_police_cleared_badge_needs_approval(client, worker_factory, ops_user, buyer):
    worker = await worker_factory(TradeEnum.PLUMBING, "Nkulumane")
    await _submit_id(client, worker)
    await _approve_id(client, ops_user, worker)
    body = await _submit_clearance(client, worker)
    assert body["police_clearance_status"] == "PENDING"
    assert (await _profile(client, buyer, worker))["has_police_clearance"] is False

    issued = (utcnow() - timedelta(days=30)).date()
    response = await client.post(
        f"/ops/vetting/{worker.id}/police-clearance",
        json={"decision": "APPROVE", "issued_on": issued.isoformat()},
        headers=auth_headers(ops_user),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["police_clearance_status"] == "VERIFIED"
    assert body["has_police_clearance"] is True
    assert body["police_clearance_expires_on"] == (issued + timedelta(days=365)).isoformat()
    assert (await _profile(client, buyer, worker))["has_police_clearance"] is True


async def test_clearance_alone_no_longer_counts_as_identity(client, worker_factory):
    worker = await worker_factory(TradeEnum.PLUMBING, "Nkulumane")

    body = await _submit_clearance(client, worker)

    assert body["grade"] == "REGISTERED"


async def test_clearance_needs_a_verified_id_first(client, worker_factory, ops_user):
    worker = await worker_factory(TradeEnum.PLUMBING, "Nkulumane")
    await _submit_clearance(client, worker)

    response = await client.post(
        f"/ops/vetting/{worker.id}/police-clearance",
        json={"decision": "APPROVE", "issued_on": utcnow().date().isoformat()},
        headers=auth_headers(ops_user),
    )

    assert response.status_code == 409


async def test_old_or_future_certificates_are_refused(client, worker_factory, ops_user):
    worker = await worker_factory(TradeEnum.PLUMBING, "Nkulumane")
    await _submit_id(client, worker)
    await _approve_id(client, ops_user, worker)
    await _submit_clearance(client, worker)
    today = utcnow().date()

    for issued in (today - timedelta(days=400), today + timedelta(days=2)):
        response = await client.post(
            f"/ops/vetting/{worker.id}/police-clearance",
            json={"decision": "APPROVE", "issued_on": issued.isoformat()},
            headers=auth_headers(ops_user),
        )
        assert response.status_code == 422
