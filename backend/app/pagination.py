from dataclasses import dataclass

from fastapi import Query


@dataclass
class Pagination:
    """Validated limit/offset for a list endpoint, capped to keep responses bounded."""

    limit: int
    offset: int


def pagination_params(
    limit: int = Query(50, ge=1, le=200, description="Maximum rows to return"),
    offset: int = Query(0, ge=0, description="Rows to skip before collecting the result set"),
) -> Pagination:
    return Pagination(limit=limit, offset=offset)
