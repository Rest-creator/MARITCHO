import os
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, File, Header, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.apps.accounts.domain.entities import Person
from app.apps.accounts.interface_adapters.dependencies import get_current_user
from app.apps.media.models import MediaFileModel
from app.core.database import get_db_session

router = APIRouter(prefix="/media", tags=["media"])
MAX_PHOTO_BYTES = 2 * 1024 * 1024
MAX_AUDIO_BYTES = 1 * 1024 * 1024
ALLOWED = {
    "image/jpeg": MAX_PHOTO_BYTES,
    "image/webp": MAX_PHOTO_BYTES,
    "audio/ogg": MAX_AUDIO_BYTES,
    "audio/aac": MAX_AUDIO_BYTES,
    "audio/mp4": MAX_AUDIO_BYTES,
    "audio/x-m4a": MAX_AUDIO_BYTES,
}
MEDIA_ROOT = Path(os.getenv("MEDIA_STORAGE_PATH", "storage/media")).resolve()


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_media(
    file: UploadFile = File(...),  # noqa: B008
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    current_user: Person = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    if file.content_type not in ALLOWED:
        raise HTTPException(status_code=415, detail="Unsupported media type")
    existing = await db.scalar(
        select(MediaFileModel).where(
            MediaFileModel.owner_id == current_user.id,
            MediaFileModel.idempotency_key == idempotency_key[:128],
        )
    )
    if existing:
        return _response(existing)
    content = await file.read(ALLOWED[file.content_type] + 1)
    if len(content) > ALLOWED[file.content_type]:
        raise HTTPException(status_code=413, detail="Media file is too large")
    media_id = uuid.uuid4()
    suffix = {
        "image/jpeg": ".jpg",
        "image/webp": ".webp",
        "audio/ogg": ".ogg",
        "audio/aac": ".aac",
        "audio/mp4": ".m4a",
        "audio/x-m4a": ".m4a",
    }[file.content_type]
    MEDIA_ROOT.mkdir(parents=True, exist_ok=True)
    name = f"{media_id}{suffix}"
    (MEDIA_ROOT / name).write_bytes(content)
    model = MediaFileModel(
        id=media_id,
        owner_id=current_user.id,
        idempotency_key=idempotency_key[:128],
        storage_name=name,
        content_type=file.content_type,
        size_bytes=len(content),
        created_at=datetime.utcnow(),
    )
    db.add(model)
    await db.commit()
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
