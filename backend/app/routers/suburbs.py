from collections.abc import Sequence

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db_session
from app.models import Suburb
from app.pagination import Pagination, pagination_params
from app.schemas import SuburbOut

router = APIRouter(prefix="/suburbs", tags=["suburbs"])


@router.get("", response_model=list[SuburbOut])
async def list_suburbs(
    pagination: Pagination = Depends(pagination_params),
    db: AsyncSession = Depends(get_db_session),
) -> Sequence[Suburb]:
    """Public reference data: known suburbs and their centroids, for building
    a suburb picker (icons/list) client-side rather than free-text entry."""
    result = await db.execute(
        select(Suburb).order_by(Suburb.name).limit(pagination.limit).offset(pagination.offset)
    )
    return result.scalars().all()
