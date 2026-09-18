from fastapi import APIRouter, Depends

from app.apps.suburbs.domain.services import ListSuburbsUseCase
from app.apps.suburbs.interface_adapters.dependencies import get_list_suburbs_use_case
from app.apps.suburbs.interface_adapters.schemas import SuburbOut
from app.core.pagination import Pagination, pagination_params

router = APIRouter(prefix="/suburbs", tags=["suburbs"])


@router.get("", response_model=list[SuburbOut])
async def list_suburbs(
    pagination: Pagination = Depends(pagination_params),
    use_case: ListSuburbsUseCase = Depends(get_list_suburbs_use_case),
) -> list[SuburbOut]:
    """Public reference data: known suburbs and their centroids, for building
    a suburb picker (icons/list) client-side rather than free-text entry."""
    suburbs = await use_case.execute(limit=pagination.limit, offset=pagination.offset)
    return [SuburbOut.model_validate(suburb, from_attributes=True) for suburb in suburbs]
