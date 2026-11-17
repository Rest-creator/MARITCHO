from pathlib import Path

import pytest

from app.apps.media import router as media_router
from tests.conftest import auth_headers

JPEG_BYTES = b"\xff\xd8\xff\xe0" + b"\x00" * 64 + b"\xff\xd9"


@pytest.fixture
def media_root(tmp_path, monkeypatch) -> Path:
    """Each test writes to its own temp dir instead of the repo's storage/."""
    root = tmp_path / "media"
    monkeypatch.setattr(media_router, "MEDIA_ROOT", root)
    return root


async def test_photo_upload_stores_jpeg_and_owner_can_download(client, buyer, media_root):
    response = await client.post(
        "/media/upload",
        headers={**auth_headers(buyer), "Idempotency-Key": "photo-1"},
        files={"file": ("photo.jpg", JPEG_BYTES, "image/jpeg")},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["content_type"] == "image/jpeg"
    assert body["size_bytes"] == len(JPEG_BYTES)
    assert len(list(media_root.iterdir())) == 1

    download = await client.get(body["url"], headers=auth_headers(buyer))
    assert download.status_code == 200
    assert download.content == JPEG_BYTES


async def test_repeating_an_upload_with_the_same_key_returns_the_same_file(
    client, buyer, media_root
):
    headers = {**auth_headers(buyer), "Idempotency-Key": "photo-retry"}
    first = await client.post(
        "/media/upload", headers=headers, files={"file": ("p.jpg", JPEG_BYTES, "image/jpeg")}
    )
    second = await client.post(
        "/media/upload", headers=headers, files={"file": ("p.jpg", JPEG_BYTES, "image/jpeg")}
    )

    assert first.status_code == second.status_code == 201
    assert first.json()["id"] == second.json()["id"]
    assert len(list(media_root.iterdir())) == 1


async def test_unwritable_storage_gives_a_clear_503_not_a_bare_500(
    client, buyer, tmp_path, monkeypatch
):
    # A regular file where the media directory should be: mkdir/write fail
    # with an OSError, like a root-owned volume does for the `app` user.
    blocker = tmp_path / "not-a-directory"
    blocker.write_text("x")
    monkeypatch.setattr(media_router, "MEDIA_ROOT", blocker / "media")

    response = await client.post(
        "/media/upload",
        headers={**auth_headers(buyer), "Idempotency-Key": "photo-unwritable"},
        files={"file": ("photo.jpg", JPEG_BYTES, "image/jpeg")},
    )

    assert response.status_code == 503
    assert response.headers["content-type"].startswith("application/json")
    assert "couldn't save your photo" in response.json()["detail"]


async def test_empty_and_unsupported_files_are_rejected_with_clear_errors(
    client, buyer, media_root
):
    empty = await client.post(
        "/media/upload",
        headers={**auth_headers(buyer), "Idempotency-Key": "photo-empty"},
        files={"file": ("photo.jpg", b"", "image/jpeg")},
    )
    assert empty.status_code == 400

    heic = await client.post(
        "/media/upload",
        headers={**auth_headers(buyer), "Idempotency-Key": "photo-heic"},
        files={"file": ("photo.heic", b"HEIC", "image/heic")},
    )
    assert heic.status_code == 415
