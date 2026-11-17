import os
import uuid
from datetime import UTC, datetime
from pathlib import Path

from fastapi import APIRouter, Depends, File, Header, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.apps.accounts.domain.entities import Person
from app.apps.accounts.interface_adapters.dependencies import get_current_user
from app.apps.media.models import MediaFileModel
from app.core.database import get_db_session
from app.core.telemetry import logger

router = APIRouter(prefix="/media", tags=["media"])
MAX_PHOTO_BYTES = 2 * 1024 * 1024
MAX_AUDIO_BYTES = 1 * 1024 * 1024
MEDIA_TYPES = {
    "image/jpeg": (MAX_PHOTO_BYTES, ".jpg"),
    "image/webp": (MAX_PHOTO_BYTES, ".webp"),
    "audio/webm": (MAX_AUDIO_BYTES, ".webm"),
    "audio/ogg": (MAX_AUDIO_BYTES, ".ogg"),
    "audio/aac": (MAX_AUDIO_BYTES, ".aac"),
    "audio/mp4": (MAX_AUDIO_BYTES, ".m4a"),
    "audio/x-m4a": (MAX_AUDIO_BYTES, ".m4a"),
}
MEDIA_ROOT = Path(os.getenv("MEDIA_STORAGE_PATH", "storage/media")).resolve()


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_media(
    file: UploadFile = File(...),  # noqa: B008
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    current_user: Person = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    content_type = (file.content_type or "").split(";")[0].strip().lower()
    if content_type not in MEDIA_TYPES:
        raise HTTPException(status_code=415, detail="Unsupported media type")
    max_bytes, suffix = MEDIA_TYPES[content_type]
    existing = await db.scalar(
        select(MediaFileModel).where(
            MediaFileModel.owner_id == current_user.id,
            MediaFileModel.idempotency_key == idempotency_key[:128],
        )
    )
    if existing:
        return _response(existing)
    content = await file.read(max_bytes + 1)
    if len(content) > max_bytes:
        raise HTTPException(status_code=413, detail="Media file is too large")
    if not content:
        raise HTTPException(status_code=400, detail="The file is empty")

    media_id = uuid.uuid4()
    name = f"{media_id}{suffix}"
    path = MEDIA_ROOT / name
    try:
        MEDIA_ROOT.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    except OSError as error:
        # e.g. a media volume the API user can't write to, or a full disk.
        # Previously an uncaught 500 with a plain-text body.
        logger.exception(
            f"media upload could not be stored user_id={current_user.id}",
            extra={
                "audit": {
                    "event": "media_store_failed",
                    "user_id": str(current_user.id),
                    "media_root": str(MEDIA_ROOT),
                    "errno": error.errno,
                }
            },
        )
        raise HTTPException(
            status_code=503,
            detail="We couldn't save your photo right now. Please try again in a moment.",
        ) from error

    model = MediaFileModel(
        id=media_id,
        owner_id=current_user.id,
        idempotency_key=idempotency_key[:128],
        storage_name=name,
        content_type=content_type,
        size_bytes=len(content),
        created_at=datetime.now(UTC),
    )
    db.add(model)
    try:
        await db.commit()
    except IntegrityError:
        # Two requests with the same idempotency key raced (double tap, or a
        # retry while the first was still in flight): return the winner.
        await db.rollback()
        path.unlink(missing_ok=True)
        winner = await db.scalar(
            select(MediaFileModel).where(
                MediaFileModel.owner_id == current_user.id,
                MediaFileModel.idempotency_key == idempotency_key[:128],
            )
        )
        if winner is None:
            raise
        return _response(winner)
    except Exception:
        path.unlink(missing_ok=True)
        raise
    return _response(model)


def _response(model: MediaFileModel) -> dict[str, object]:
    return {
        "id": str(model.id),
        "content_type": model.content_type,
        "size_bytes": model.size_bytes,
        "url": f"/media/{model.id}",
    }


@router.get("/{media_id}")
async def download_media(
    media_id: uuid.UUID,
    current_user: Person = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> FileResponse:
    model = await db.get(MediaFileModel, media_id)
    if model is None or (model.owner_id != current_user.id and current_user.role.value != "OPS"):
        raise HTTPException(status_code=404, detail="Media not found")
    path = (MEDIA_ROOT / model.storage_name).resolve()
    if MEDIA_ROOT not in path.parents or not path.is_file():
        raise HTTPException(status_code=404, detail="Media not found")
    return FileResponse(path, media_type=model.content_type)
