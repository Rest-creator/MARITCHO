# Maricho Software Requirements Specification (SRS)

## 1. System Architecture Constraints
Maricho is built to operate under severe physical constraints: inexpensive Android phones, tiny data bundles, and frequent power/signal losses.

- **Offline-First Architecture:** The client applications (PWA and native) must queue state mutations (check-ins, photo uploads, quotes) locally when offline.
- **Data Conservation (Light Mode):** The UI must default to text-first. Images are only downloaded on explicit request. All uploaded photographs must be aggressively compressed on the client device before transmission.
- **API Transport:** The backend will expose a REST API prioritizing structured JSON payloads.
- **Infrastructure:** Self-hosted containerized deployment.

## 2. Non-Functional Requirements (NFRs)

### 2.1. Performance & Latency (SLOs)
- **API Response Time:** 99% of API requests (excluding file uploads) must resolve within 50ms.
- **Connection Pooling:** The PostgreSQL database must utilize an asynchronous connection pool (e.g., `pool_size=10`, `max_overflow=5`, `pool_recycle=1800`) sized against a documented connection budget, to prevent starvation during traffic spikes both within a single instance and across horizontally-scaled replicas.
- **Background Jobs:** Heavy tasks (image processing, notifications) must be offloaded to asynchronous background workers (e.g., Celery/BullMQ) with strict idempotency and Dead Letter Queues (DLQ).

### 2.2. Observability & Tracing
- **Tracing:** All backend services must implement OpenTelemetry distributed tracing (W3C Trace Context).
- **Logging:** Structured JSON logging is mandatory, injecting `trace_id` and `span_id` into every log entry.
- **Health Checks:** Services must expose separated `/health/live` (process check) and `/health/ready` (dependency check, e.g., DB ping) endpoints.

### 2.3. Security & Compliance
- **Authentication:** OAuth2/JWT based authentication.
- **Authorization:** Granular RBAC enforcing that users can only access their own ledger and record entries.
- **Data Sanitization:** All incoming requests (especially voice-to-text transcripts and text descriptions) must be sanitized to prevent injection attacks.
- **Containers:** Docker images must run as non-root users.

## 3. Behavioral Acceptance Criteria for NFRs (BDD)

| NFR Category | Scenario | Given | When | Then |
| :--- | :--- | :--- | :--- | :--- |
| **Offline Sync** | Worker checks in without signal | The app detects no internet connection | The worker taps "Check In" | The app displays "Saved locally" and queues the timestamp for background sync. |
| **Data Usage** | Viewing job history on cellular | The user has "Light mode" enabled | The user opens a past job | The app shows text only and requires a tap to load the attached photo. |
| **Performance** | API Latency validation | The system is under normal load | A client requests the worker shortlist | The API must return the response in `< 50ms`. |
| **Resilience** | Database connection stress | The system receives a burst of 100 requests | The backend processes the requests | The connection pool must queue requests without dropping connections or exceeding `max_overflow`. |
| **Health** | Readiness probe failure | The database is temporarily unreachable | The load balancer queries `/health/ready` | The API must return `503 Service Unavailable` immediately. |
