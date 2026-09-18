# ADR 007: Clean Architecture with Domain-Based Apps

## Status
Accepted and implemented (backend restructuring; no schema or HTTP-contract changes — see "Consequences")

## Context
The backend had grown as a flat modular monolith: one `app/models.py` (409 lines, 18 ORM classes across five domains), one `app/schemas.py` (428 lines, ~36 Pydantic classes), and per-domain router files (`app/routers/jobs.py`, `workers.py`, `crew_orders.py`, `crews.py`, `suburbs.py`, `payment_gateways.py`) that talked directly to SQLAlchemy inside the HTTP handler, alongside free-floating logic modules (`matching.py`, `crew_matching.py`, `ledger.py`, `standing.py`, `vetting.py`, `grading.py`, `geo.py`, `ecocash.py`). Business rules, persistence, and HTTP concerns were interleaved in the same functions, and there was no enforced boundary between domains — a jobs-router function could reach into worker or crew tables directly.

As more domains accreted (multi-currency ledger, progressive vetting, crew hire, EcoCash payments), this made it harder to see which rules belonged to which domain, and harder to change one domain's persistence without touching its business logic.

## Decision
Restructure into **Clean Architecture** combined with **domain-based "apps"**, mirroring the platform's existing domain boundaries:

- `app/core/` — framework/infrastructure every app depends on (DB session factory, JWT primitives, pagination, structured logging, the domain-exception-to-HTTP translation boundary). Core never depends on an app.
- `app/shared_kernel/` — framework-free vocabulary genuinely shared by 2+ apps: enums backing the same Postgres type across different apps' tables (`LedgerEntryTypeEnum`, `CurrencyEnum`, `TradeEnum`, `GradeEnum`, `RoleEnum`, `DistanceBandEnum`), pure functions with no I/O (`geo.py`, `grading.py`, `text.py`), and cross-app port ABCs (`WorkerAvailabilityPort`, `PaymentCollectionPort`, `SuburbLookupPort`, `WorkerJobStatsPort`, `WorkerMatchingProfilePort`) plus their value objects.
- `app/apps/{accounts,suburbs,payments,workers,jobs,crews}/` — one package per domain, each with:
  - `domain/` — framework-free entities (plain dataclasses) and repository/port interfaces (`abc.ABC`), plus `services.py`: one use-case class per business operation, holding exactly the logic that used to live inline in a router function.
  - `infrastructure/` — SQLAlchemy models and concrete repository implementations satisfying the domain interfaces. The only layer allowed to import `sqlalchemy`.
  - `interface_adapters/` — Pydantic schemas, FastAPI routers (parse → call use case → serialize, no business logic), and per-app dependency-injection factories.
- `app/main.py` — the composition root: includes every app's router, registers the exception-translation handlers, and is where cross-app port implementations get wired to their consumers.

Two deliberate, documented exceptions to the "apps are isolated" rule:
1. **`accounts` and `workers` are foundational direct dependencies.** Every app may import `accounts.domain.repositories.PersonRepository` directly (identity is needed everywhere), and `jobs`/`crews` import `workers.domain.services.RecomputeStandingUseCase` and its repository directly rather than routing standing recomputation through a new port — this was judged a legitimate reuse of an existing use case, not a new abstraction boundary to build.
2. **A `UnitOfWork` abstraction** (`shared_kernel/unit_of_work.py` + `core/unit_of_work.py`) is a pragmatic exception to "domain never touches infrastructure": transaction commit/rollback is treated as an application-layer concern. Without it, either every repository method would need to commit independently (breaking atomicity across multi-step use cases) or the domain layer would need to import `AsyncSession` directly (violating the dependency rule).

Cross-app data needs that don't fit the "foundational dependency" pattern go through `shared_kernel` ports: `WorkerAvailabilityPort` (jobs' `SqlAlchemyJobRepository` implements it; crews' matching and workers' standing endpoint consume it), `PaymentCollectionPort` (payments' `EcoCashGateway` implements it; jobs/crews booking consume it), `SuburbLookupPort` (suburbs implements it; jobs/crews/workers consume it), `WorkerMatchingProfilePort` and `WorkerJobStatsPort` (workers/jobs implement narrow, purpose-built adapters so jobs/crews matching gets batched queries instead of N+1 round-trips across the app boundary).

## Consequences
- **Positive:** Business rules are now readable independently of persistence and HTTP concerns (each use case is a single class with an `execute()` method); a domain's persistence can change without touching its business logic; cross-app coupling is explicit and narrow (named ports) instead of implicit (direct ORM access from another domain's router).
- **Positive:** The HTTP contract (all routes, status codes, request/response shapes — verified against `docs/architecture/openapi.yaml`), the Postgres schema (verified with `alembic check` after a full `downgrade base` → `upgrade head` cycle: no drift), and all business behavior are unchanged — this was a pure internal reorganization, not a rewrite.
- **Negative:** More files and more total lines for the same behavior (a domain now has a dataclass entity *and* an ORM model, a repository interface *and* an implementation) — coverage percentage against the same test suite therefore reads lower than the old flat structure's, even though the same code paths are exercised (see the coverage-tooling caveat below).
- **Negative:** Two apps building simultaneously can reach for the same cross-app port name from different directions; this needs the port to be added to `shared_kernel/ports.py` (or agreed on) before both sides are built, not discovered independently.
- **Tooling caveat, not an architecture cost:** SQLAlchemy's async engine bridges each blocking DBAPI call through a `greenlet` switch; `coverage.py`'s default `sys.settrace`-based tracer loses attribution for everything after the first `await db.*` call in a frame unless `concurrency = ["greenlet"]` is set in `[tool.coverage.run]` (`pyproject.toml`). Without it, most of the domain/use-case layer reads as uncovered even when it demonstrably executes (verified by temporarily wrapping a use case's `execute()` and confirming the call happens) — this is a coverage-measurement gap, not a test-coverage gap, and was corrected as part of this restructuring since the new layer split made it visible for the first time.

## Related
- `docs/backlog.md`
- `docs/architecture/system_design.md` §2 (architecture overview) — updated with a pointer to this ADR
- Prior ADRs (002–006), whose decisions are carried forward unchanged in the new structure, not revisited
