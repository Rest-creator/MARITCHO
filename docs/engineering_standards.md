# Engineering Standards Manual

## 1. Code Formatting & Linting
- **Backend (Python/FastAPI):** We use **Ruff** for linting and formatting, and **MyPy** for strict static type checking.
- **Frontend (React Native/Expo):** We use **ESLint** (with Prettier) and strict **TypeScript**.
- **Enforcement:** Code must pass local linters (`ruff check .`, `mypy .`) before any commit. 

## 2. Telemetry & Observability
- **Distributed Tracing:** All backend services must implement OpenTelemetry (W3C Trace Context).
- **Structured Logging:** Standard `logging` must output JSON or structured text containing `trace_id` and `span_id`.
  - Format: `%(asctime)s [%(levelname)s] [trace_id=%(otelTraceID)s span_id=%(otelSpanID)s] %(name)s: %(message)s`
- **Health Checks:** `/health/live` (process check) and `/health/ready` (dependency check, e.g., PostgreSQL/Redis ping) must be implemented.

## 3. Database Integrity
- **Migrations:** Use **Alembic** for all schema changes. Never execute manual SQL in production.
- **Connection Pooling:** Use SQLAlchemy AsyncEngine with `pool_size=10`, `max_overflow=5`, `pool_recycle=1800`, and `pool_pre_ping=True` (15 connections/instance).
  - **Connection budget:** size per-instance pool so that
    `replica_count × (pool_size + max_overflow) ≤ Postgres max_connections`,
    leaving headroom for migrations, `psql`/monitoring, and a future
    background-worker tier. At the current default `max_connections=100`
    and 15/instance, that supports up to ~6 replicas with 10 connections of
    headroom. Before running more replicas than that, or before lowering
    `max_connections`, re-run this formula — don't just add replicas and
    assume the pool scales with them.
- **Immutability:** No `UPDATE` or `DELETE` allowed on `ledger_entries` or `record_entries`.

## 4. Testing Contract
- **Test-Driven Development (TDD):** Automated tests (Pytest/Jest) must be written mapping directly to the BDD scenarios in the PRD/SRS.
- **Coverage:** Minimum 85% test coverage required.
