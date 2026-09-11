# ADR 001: Core Technology Stack & Offline Strategy

## Status
Accepted

## Context
Maricho operates in Bulawayo, Zimbabwe, where users face intermittent power, expensive cellular data, and utilize low-end Android devices. The system requires an offline-first architecture, highly concurrent backend processing for job matching, and strict relational data integrity for ledger management. We must also align with our SDLC and Engineering Standards (ISO 12207 / NIST SSDF).

## Decision
1. **Backend:** We will use **FastAPI (Python)**. It provides native async support, out-of-the-box OpenAPI v3 generation, and excellent Pydantic validation to protect against malformed data inputs.
2. **Database:** We will use **PostgreSQL**. The immutable nature of Maricho's "Record Entry" and "Ledger Entry" requires ACID compliance and strong relational constraints.
3. **Database Pooling:** We will enforce async connection pooling (`pool_size=10`, `max_overflow=5`, `pool_pre_ping=True`) to prevent connection starvation during network reconnection spikes. Sized per instance against a connection budget (`replica_count × pool ≤ Postgres max_connections`) — see `docs/engineering_standards.md` §3.
4. **Mobile Client:** We will use **React Native via Expo**. This allows us to build robust offline-first synchronization using local SQLite/AsyncStorage, and push Over-The-Air (OTA) updates to bypass app store review delays.
5. **Background Jobs:** We will use **Redis + Celery (or ARQ)**. Heavy tasks like image compression, WhatsApp webhook processing, and dispute notification routing must not block the synchronous HTTP threads.
   - **Implementation status (2026-09-11):** Deferred. Redis is provisioned
     (`docker-compose.yml`) but no queue library, task, or worker process
     has been built — it is only pinged for liveness today. This decision
     still holds for *when* an async workload exists; it is intentionally
     not built ahead of one, since every backend feature shipped so far
     (matching, standing recomputation, ledger writes) runs fast enough
     synchronously. Revisit once photo upload/compression, WhatsApp webhook
     processing, or another genuinely heavy task is actually scoped — see
     `docs/backlog.md`.

## Consequences
- **Positive:** FastAPI ensures API contracts (OpenAPI) are strictly enforced. PostgreSQL guarantees ledger safety. Expo allows rapid iteration and offline syncing.
- **Negative/Risks:** Maintaining offline sync logic (conflict resolution when a worker checks in while a buyer cancels) introduces significant state-management complexity on the client. We will mitigate this with "Design for the worker's worst day" rules (e.g., if worker checks in offline before buyer cancels, worker keeps deposit).
