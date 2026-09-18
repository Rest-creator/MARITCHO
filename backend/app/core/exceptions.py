"""Domain exception hierarchy + the FastAPI translation boundary (ADR-007).

Use cases (`apps/*/domain/services.py`) raise these instead of
`fastapi.HTTPException` — that's what keeps the domain/application layers
framework-free per Clean Architecture's dependency rule. Routers and
dependencies (interface_adapters) may still raise `HTTPException` directly
for pure request-shape/auth concerns (e.g. `RequireRole`), since those
already live in the outermost layer.

`register_exception_handlers()` is called once from `main.py` and maps
each exception type to the exact HTTP status code the old routers used to
raise directly — response bodies are unchanged (`{"detail": <message>}`).
"""

from collections.abc import Callable

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class DomainError(Exception):
    """Base for all domain/use-case exceptions."""


class NotFoundError(DomainError):
    """-> 404"""


class ForbiddenError(DomainError):
    """-> 403"""


class ConflictError(DomainError):
    """-> 409"""


class ValidationConflictError(DomainError):
    """-> 422: input is syntactically valid but semantically wrong (e.g. a
    referenced ID doesn't resolve to the expected kind of record, or a
    computed value fails a business-rule comparison)."""


class BadGatewayError(DomainError):
    """-> 502: an external dependency (e.g. a payment gateway) failed."""


class ServiceUnavailableError(DomainError):
    """-> 503: an external dependency isn't configured yet."""


class IntegrityConflictError(DomainError):
    """Raised by UnitOfWork.commit() when the persistence layer rejects a
    write due to a uniqueness/integrity constraint (e.g. a duplicate
    skill/crew/vouch). Use cases are expected to catch this and re-raise a
    ConflictError with a context-specific message; mapped to 409 here too
    as a fallback if one doesn't."""


_STATUS_BY_EXCEPTION: dict[type[DomainError], int] = {
    NotFoundError: 404,
    ForbiddenError: 403,
    ConflictError: 409,
    ValidationConflictError: 422,
    BadGatewayError: 502,
    ServiceUnavailableError: 503,
    IntegrityConflictError: 409,
}


def _make_handler(status_code: int) -> Callable[[Request, Exception], JSONResponse]:
    def _handler(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(status_code=status_code, content={"detail": str(exc)})

    return _handler


def register_exception_handlers(app: FastAPI) -> None:
    for exc_type, status_code in _STATUS_BY_EXCEPTION.items():
        app.add_exception_handler(exc_type, _make_handler(status_code))
