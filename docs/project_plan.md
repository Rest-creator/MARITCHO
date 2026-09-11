# Maricho Project Plan & Risk Register

## 1. Project Milestones

- **Milestone 1: Backend Foundation (Weeks 1-2)**
  - Delivery of a healthy, telemetry-instrumented FastAPI backend with automated database migrations and CI/CD linting checks.
- **Milestone 2: Core Domain Logic (Weeks 3-4)**
  - The matching engine, job lifecycles, and immutable ledger entries are functional and backed by integration tests.
- **Milestone 3: Client Resilience (Weeks 5-6)**
  - The Expo app can successfully queue a job check-in and photos offline, syncing automatically when a connection is restored.
- **Milestone 4: Staging & UAT (Week 7)**
  - Blue-Green deployment to staging; end-to-end tests passing; field-testing with simulated latency and packet loss.

## 2. Risk Register

| Risk ID | Description | Impact | Probability | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **RSK-001** | **State Conflict:** Worker checks in offline, but buyer cancels job online simultaneously. | High | Medium | Implement "Design for worker's worst day" logic. If a worker checks in before receiving the cancellation ping, they keep the deposit. |
| **RSK-002** | **Connection Starvation:** Backend crashes due to maxing out database connections during a network reconnection burst, or across horizontally-scaled replicas exhausting Postgres's `max_connections`. | High | High | Enforce strict asynchronous connection pooling in SQLAlchemy (`pool_size=10`, `max_overflow=5`), sized per instance against a documented connection budget (`docs/engineering_standards.md` §3) so replica count and Postgres's connection ceiling stay reconciled. |
| **RSK-003** | **Data Costs:** Uploading high-res job photos exhausts worker data bundles. | Medium | High | Aggressive on-device image compression prior to queuing the upload. UI defaults to "Light Mode". |
| **RSK-004** | **AI Reviewer Trap:** Blind trust in AI-generated code leads to subtle ledger logic flaws. | High | Medium | Mandate strict BDD Test-Driven Development (TDD). Tests must be written and peer-reviewed before implementation logic is finalized. |
