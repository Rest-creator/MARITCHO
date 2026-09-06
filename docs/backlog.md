# Maricho Sprint Backlog

## Sprint 1: Infrastructure & Core API

| Task ID | Status | Priority | Description | Dependencies | Assignee |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **BACK-001** | `TODO` | High | Initialize FastAPI project structure with strict linting (Ruff/MyPy). | None | - |
| **BACK-002** | `TODO` | High | Implement OpenTelemetry distributed tracing and structured JSON logging. | BACK-001 | - |
| **BACK-003** | `DONE` | High | Setup Alembic and execute initial `schema.sql` database migrations. | BACK-001 | - |
| **BACK-004** | `DONE` | High | Implement `/health/live` and `/health/ready` (DB & Redis ping) endpoints. | BACK-001, BACK-003 | - |
| **BACK-005** | `DONE` | Medium | Implement core authentication & RBAC dependency injection. | BACK-003 | - |

## Sprint 2: Matching Engine & Ledger

| Task ID | Status | Priority | Description | Dependencies | Assignee |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **CORE-001** | `TODO` | High | Implement Job Request ingestion endpoint (audio/text). | BACK-005 | - |
| **CORE-002** | `TODO` | High | Build the worker matching algorithm (filtering by trade, suburb, standing, and availability). | CORE-001 | - |
| **CORE-003** | `TODO` | High | Implement Ledger logic for Deposit Holding and Balance Commitment. | CORE-002 | - |
| **CORE-004** | `TODO` | Medium | Implement dispute resolution workflow (freezing ledger, attaching photos). | CORE-003 | - |

## Sprint 3: Offline-First Client

| Task ID | Status | Priority | Description | Dependencies | Assignee |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **APP-001** | `TODO` | High | Scaffold Expo React Native app with local SQLite/AsyncStorage sync engine. | None | - |
| **APP-002** | `TODO` | High | Build offline-capable "Check-In" and "Upload Photo" queueing mechanism. | APP-001 | - |
| **APP-003** | `TODO` | Medium | Implement Light Mode UI components (text-first, tap-to-load images). | APP-001 | - |
