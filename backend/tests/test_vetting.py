from app.shared_kernel.enums import GradeEnum, TradeEnum
from tests.conftest import auth_headers


async def _get_vetting(client, worker):
    response = await client.get("/workers/me/vetting", headers=auth_headers(worker))
    assert response.status_code == 200
    return response.json()


async def test_fresh_worker_starts_registered_with_no_evidence(client, worker_factory):
    worker = await worker_factory(TradeEnum.PLUMBING, "Nkulumane")

    body = await _get_vetting(client, worker)

    assert body["grade"] == "REGISTERED"
    assert body["id_photo_url"] is None
    assert body["id_submitted_at"] is None
    assert body["reference_count"] == 0
    assert body["vouch_count"] == 0


async def test_submitting_id_photo_promotes_to_identified(client, worker_factory):
    worker = await worker_factory(TradeEnum.PLUMBING, "Nkulumane")

    response = await client.post(
        "/workers/me/vetting/id-photo",
        json={"id_photo_url": "https://example.com/id.jpg"},
        headers=auth_headers(worker),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["grade"] == "IDENTIFIED"
    assert body["id_photo_url"] == "https://example.com/id.jpg"
    assert body["id_submitted_at"] is not None


async def test_reference_without_id_photo_does_not_promote(client, worker_factory):
    worker = await worker_factory(TradeEnum.PLUMBING, "Nkulumane")

    response = await client.post(
        "/workers/me/references",
        json={"name": "Mai Ncube", "phone": "+263771234567"},
        headers=auth_headers(worker),
    )
    assert response.status_code == 201

    body = await _get_vetting(client, worker)
    assert body["grade"] == "REGISTERED"
    assert body["reference_count"] == 1


async def test_id_photo_plus_reference_promotes_to_apprentice(client, worker_factory):
    worker = await worker_factory(TradeEnum.PLUMBING, "Nkulumane")

    await client.post(
        "/workers/me/vetting/id-photo",
        json={"id_photo_url": "https://example.com/id.jpg"},
        headers=auth_headers(worker),
    )
    response = await client.post(
        "/workers/me/references",
        json={"name": "Mai Ncube", "phone": "+263771234567"},
        headers=auth_headers(worker),
    )

    assert response.status_code == 201
    body = await _get_vetting(client, worker)
    assert body["grade"] == "APPRENTICE"


async def test_list_my_references_returns_submitted_references(client, worker_factory):
    worker = await worker_factory(TradeEnum.PLUMBING, "Nkulumane")
    await client.post(
        "/workers/me/references",
        json={"name": "Mai Ncube", "phone": "+263771234567"},
        headers=auth_headers(worker),
    )

    response = await client.get("/workers/me/references", headers=auth_headers(worker))

    assert response.status_code == 200
    references = response.json()
    assert len(references) == 1
    assert references[0]["name"] == "Mai Ncube"
    assert references[0]["worker_id"] == str(worker.id)


async def test_vouch_from_journeyman_promotes_to_journeyman(client, worker_factory):
    apprentice = await worker_factory(TradeEnum.PLUMBING, "Nkulumane")
    master = await worker_factory(
        TradeEnum.PLUMBING, "Nkulumane", grade=GradeEnum.JOURNEYMAN
    )

    response = await client.post(
        "/workers/me/vouches",
        json={"worker_id": str(apprentice.id)},
        headers=auth_headers(master),
    )

    assert response.status_code == 201
    body = await _get_vetting(client, apprentice)
    assert body["grade"] == "JOURNEYMAN"
    assert body["vouch_count"] == 1


async def test_three_journeyman_vouches_promote_to_expert(client, worker_factory):
    apprentice = await worker_factory(TradeEnum.PLUMBING, "Nkulumane")
    masters = [
        await worker_factory(TradeEnum.PLUMBING, "Nkulumane", grade=GradeEnum.JOURNEYMAN)
        for _ in range(3)
    ]

    for master in masters:
        response = await client.post(
            "/workers/me/vouches",
            json={"worker_id": str(apprentice.id)},
            headers=auth_headers(master),
        )
        assert response.status_code == 201

    body = await _get_vetting(client, apprentice)
    assert body["grade"] == "EXPERT"
    assert body["vouch_count"] == 3


async def test_vouch_from_below_journeyman_is_rejected(client, worker_factory):
    apprentice = await worker_factory(TradeEnum.PLUMBING, "Nkulumane")
    peer = await worker_factory(
        TradeEnum.PLUMBING, "Nkulumane", grade=GradeEnum.APPRENTICE
    )

    response = await client.post(
        "/workers/me/vouches",
        json={"worker_id": str(apprentice.id)},
        headers=auth_headers(peer),
    )

    assert response.status_code == 403


async def test_self_vouch_is_rejected(client, worker_factory):
    worker = await worker_factory(
        TradeEnum.PLUMBING, "Nkulumane", grade=GradeEnum.JOURNEYMAN
    )

    response = await client.post(
        "/workers/me/vouches",
        json={"worker_id": str(worker.id)},
        headers=auth_headers(worker),
    )

    assert response.status_code == 422


async def test_duplicate_vouch_is_rejected(client, worker_factory):
    apprentice = await worker_factory(TradeEnum.PLUMBING, "Nkulumane")
    master = await worker_factory(
        TradeEnum.PLUMBING, "Nkulumane", grade=GradeEnum.JOURNEYMAN
    )

    first = await client.post(
        "/workers/me/vouches",
        json={"worker_id": str(apprentice.id)},
        headers=auth_headers(master),
    )
    assert first.status_code == 201

    second = await client.post(
        "/workers/me/vouches",
        json={"worker_id": str(apprentice.id)},
        headers=auth_headers(master),
    )

    assert second.status_code == 409


async def test_vouching_for_a_non_worker_is_rejected(client, worker_factory, buyer):
    master = await worker_factory(
        TradeEnum.PLUMBING, "Nkulumane", grade=GradeEnum.JOURNEYMAN
    )

    response = await client.post(
        "/workers/me/vouches",
        json={"worker_id": str(buyer.id)},
        headers=auth_headers(master),
    )

    assert response.status_code == 422


async def test_vouching_for_unknown_worker_id_is_rejected(client, worker_factory):
    master = await worker_factory(
        TradeEnum.PLUMBING, "Nkulumane", grade=GradeEnum.JOURNEYMAN
    )

    response = await client.post(
        "/workers/me/vouches",
        json={"worker_id": "00000000-0000-0000-0000-000000000000"},
        headers=auth_headers(master),
    )

    assert response.status_code == 422


async def test_buyer_cannot_use_vetting_endpoints(client, buyer):
    response = await client.get("/workers/me/vetting", headers=auth_headers(buyer))

    assert response.status_code == 403
