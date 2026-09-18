from abc import ABC, abstractmethod


class UnitOfWork(ABC):
    """Transaction-boundary control for a use case (ADR-007).

    A pragmatic, deliberate exception to "domain layer touches no
    infrastructure": committing/rolling back a transaction is inherently
    an application-layer concern (a use case decides what counts as one
    atomic unit of work), not a data-access concern — so mutating use
    cases depend on this narrow ABC directly, while actual queries still
    go through repositories. The SQLAlchemy `AsyncSession` itself never
    appears above the infrastructure layer (see app/core/unit_of_work.py).
    """

    @abstractmethod
    async def commit(self) -> None:
        """Raises app.core.exceptions.IntegrityConflictError if the
        underlying persistence layer rejects the write (e.g. a unique
        constraint violation) — never a raw persistence-layer exception."""

    @abstractmethod
    async def rollback(self) -> None: ...
