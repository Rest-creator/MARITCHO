# Maricho Sprint Backlog

## Sprint 1: Infrastructure & Core API

| Task ID | Status | Priority | Description | Dependencies | Assignee |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **BACK-001** | `DONE` | High | Initialize FastAPI project structure with strict linting (Ruff/MyPy). | None | - |
| **BACK-002** | `DONE` | High | Implement OpenTelemetry distributed tracing and structured JSON logging. `app/telemetry.py::JSONLogFormatter` emits one JSON object per line (timestamp, level, logger, message, trace_id, span_id, exception when present), replacing the previous formatted-text output. Scoped to the app's own logger; uvicorn's built-in access/error logging keeps its default format, unconfigured here. | BACK-001 | - |
| **BACK-003** | `DONE` | High | Setup Alembic and execute initial `schema.sql` database migrations. | BACK-001 | - |
| **BACK-004** | `DONE` | High | Implement `/health/live` and `/health/ready` (DB & Redis ping) endpoints. | BACK-001, BACK-003 | - |
| **BACK-005** | `DONE` | Medium | Implement core authentication & RBAC dependency injection. | BACK-003 | - |
| **BACK-006** | `DONE` | High | Containerize the API server itself (Dockerfile, non-root user, docker-compose `api` service, CI build+smoke-test gate). Previously only `db`/`redis` were containerized. | BACK-003 | - |
| **BACK-007** | `DEFERRED` | Low | Build the Redis/Celery-or-ARQ background-worker tier named in ADR-001 (image compression, WhatsApp webhook processing, dispute notification routing). Deliberately not started: no current workload needs offloading. Pick this up once a genuinely heavy async task (e.g. photo upload/compression) is actually scoped — don't build the worker tier speculatively ahead of it. | BACK-001 | - |
| **BACK-008** | `DEFERRED` | Low | Move distance-band matching (`app/geo.py`) off pure-Python haversine onto PostGIS (`geography` column + GIST index, distance filter pushed into SQL). Deliberately not started: correct trade-off at ~6 suburbs/small worker base today. Pick this up once Stage Two (wider Bulawayo coverage) or Stage Three (a second city) actually lands — don't add PostGIS speculatively ahead of that. | CORE-002a | - |
| **BACK-009** | `TODO` | High | Build WhatsApp Business Cloud API intake per ADR-006. Already-approved Stage One scope (`business_case.md`), not a new idea — just not started. Needs its own scoping/kickoff first: Meta Business API developer/business verification, phone number provisioning, and message-template approval are external dependencies that block work starting immediately. | BACK-005 | - |

## Sprint 2: Matching Engine & Ledger

| Task ID | Status | Priority | Description | Dependencies | Assignee |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **CORE-001** | `DONE` | High | Implement Job Request ingestion endpoint (audio/text). | BACK-005 | - |
| **CORE-002** | `DONE` | High | Build the worker matching algorithm (filtering by trade, suburb, standing, and availability). | CORE-001 | - |
| **CORE-002a** | `DONE` | Medium | Add a `suburbs` reference table (lat/long) and haversine distance-band ranking to the matching engine. | CORE-002 | - |
| **CORE-002b** | `DONE` | Medium | Worker registration endpoints (`/workers/me/skills`, `/workers/me/service-areas`, `/workers/me/standing`), so matching has real self-service data to run against. | CORE-002 | - |
| **CORE-003** | `DONE` | High | Implement Ledger logic for Deposit Holding and Balance Commitment (extended to a full booking → quote → completion lifecycle, since a deposit/commitment mechanism with no release path is unusable — REFUNDED and dispute-freeze remain CORE-004). | CORE-002 | - |
| **CORE-004** | `DONE` | Medium | Implement dispute resolution workflow (freezing ledger, attaching photos). Default resolution is a worker-initiated return visit; REFUNDED / OPS-arbitrated refunds are not yet built. | CORE-003 | - |

## Sprint 2c: Crew Hire

Not originally scoped for the current pilot stage — the business case names
a self-service "Crew Hire console" as **Stage Two** work, while Stage One
uses hand-filled crew orders. Built ahead of schedule at the user's request.

| Task ID | Status | Priority | Description | Dependencies | Assignee |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **CREW-001** | `DONE` | Medium | Crew roster management: an AGGREGATOR (crew lead) creates their crew and adds/removes WORKER members (`/crews/me`, `/crews/me/members`). | CORE-002b | - |
| **CREW-002** | `DONE` | Medium | Crew Hire booking/ordering flow: an organization (BUYER) requests N workers of a trade for a site, matched against crews with enough qualifying members, with its own book → quote → complete lifecycle and ledger (`/crew-orders/*`). No dispute/refund path, and no per-worker `RecordEntry` analog — see `database_schema_design.md`. | CREW-001, CORE-003 | - |

## Sprint 2d: Zimbabwe-Adjusted Trust & Payments Hardening

Sourced from a 2026-09-18 comparative review of similar service
marketplaces (Thumbtack, Taskrabbit, Urban Company, Angi, Airtasker,
Handy, Porch, Houzz, Checkatrade, MyBuilder, Kandua, Lynk/Eden Life,
ZiMLiNKS), re-evaluated specifically for Zimbabwe's operating conditions
rather than adopted wholesale. See ADRs 002–005 and
`database_schema_design.md` §§9–10 for the reasoning and implementation
behind each item below — all four are now `DONE`.

| Task ID | Status | Priority | Description | Dependencies | Assignee |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **LEDG-001** | `DONE` | High | Add multi-currency (`USD`/`ECOCASH`/`ZWG`) to `LEDGER_ENTRIES`/`CREW_ORDER_LEDGER_ENTRIES`, plus a real (config-gated) EcoCash collection integration for the buyer-paid deposit/fee, per ADR-002 (revised: buyer-funded, not a worker wallet — an earlier draft was caught and corrected before implementation). Admin-editable gateway config (`PAYMENT_GATEWAY_CONFIGS`), OPS endpoints, webhook receiver (`ECOCASH_CALLBACK_LOGS`). Not verified against the live EcoCash service — no real credentials exist yet. | CORE-003 | - |
| **CORE-005** | `DONE` | Medium | Split `quote_amount` into `labor_amount` + `materials_amount` on both `Job` and `CrewOrder`, per ADR-003. `quote_amount` is now computed server-side (never client-supplied) as their sum, with a DB-level `CHECK` constraint enforcing the equality. | CORE-003, CREW-002 | - |
| **CORE-006** | `DONE` | Low-Medium | Add `landmark_narrative` + optional GPS pin to `Job`/`CrewOrder` address capture, per ADR-004. Additive, nullable fields on both request payloads, gated behind the same buyer/assigned-worker/OPS access check as `address`. | CORE-001, CREW-002 | - |
| **CORE-007** | `DONE` | Medium | Build the progressive vetting-tier promotion workflow (ID photo → references → higher-tier peer vouch) that sets `Standing.grade`, per ADR-005. New `worker_vetting`/`worker_references`/`worker_vouches` tables, `app/vetting.py::recompute_grade`, and `/workers/me/vetting*`, `/workers/me/references`, `/workers/me/vouches` endpoints. Closes the still-open "nothing sets grade" gap from the architecture review — for `Standing.grade` (what matching consumes); `Skill.grade` (per-trade) remains a separate, unaddressed future scope. | CORE-002b | - |

## Sprint 3: Offline-First Client

| Task ID | Status | Priority | Description | Dependencies | Assignee |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **APP-001** | `DONE` | High | Scaffold Flutter app with local SQLite sync engine (commit `17dd4ec`), buyer and worker flows, offline-first cached reads. Mobile CI (`mobile-ci.yml`) runs format/analyze/test on Flutter 3.47.5. | None | - |
| **APP-002** | `DONE` | High | Offline "I've arrived" price confirmation (`POST /jobs/{id}/quote`) and job photos (to `/media`, shared in the job chat), saved on the phone and sent by `SyncService` when there's signal; refusals are kept and shown with "Try again". Replaces the unreachable check-in prototype, which posted to endpoints the backend never had. Photos switch on with issue #1. | APP-001 | - |
| **APP-003** | `TODO` | Medium | Light Mode UI (text-first, tap-to-load images). `TapToLoadImage` exists (`core/theme`) but no screen shows photos yet; use it once job/chat photos are displayed (needs issue #1). | APP-001 | - |
| **WEB-001** | `DONE` | High | Scaffold the Next.js PWA in `frontend/`: BFF proxy (`/api/*`, JWT in an httpOnly cookie), zod response contracts, TanStack Query cache persisted on device with offline mutation replay, app-shell service worker, design tokens from `wireframes/`. | None | - |
| **WEB-002** | `DONE` | High | Employer flow screens per the approved app UI: welcome, sign-up, home (E1), post a job + skill picker (E2/E3), applicants + hire (E4), worker profile (E5), tracking / sign-off review / dispute (E6), chat. | WEB-001 | - |
| **WEB-003** | `DONE` | High | Worker flow screens: skills + travel radius (W1), jobs near you (W2), job detail + offer (W3), my work with on-site quote and dispute response (W4). | WEB-001 | - |
| **WEB-004** | `DONE` | Medium | Upload job photos (shrunk to ≤1280 px JPEG on the phone, GPS stripped), chat photos and voice notes; uploaded media is tap-to-load. Frontend done; switches on by itself once the backend media endpoint lands (issue #1). | WEB-002 | - |
| **WEB-005** | `DONE` | Medium | 6-digit sign-in code step (autofill, auto-submit, resend countdown). Frontend done; switches on by itself once `/auth/otp/request` exists (issue #5, BACK-009); until then sign-in uses the `/token` mock. | WEB-001 | - |
| **WEB-006** | `DONE` | Medium | Playwright E2E + visual regression in CI: job lifecycle against a throwaway docker-compose backend, plus screenshots of all 13 screens from fixtures. Found #7 (offering workers missing from `/matches`). | WEB-003 | - |
| **WEB-007** | `DONE` | High | One BFF for web and mobile (ADR-009): the Next.js `/api` owns the client contract and translates to FastAPI in one place; mobile signs in and calls through it with a bearer token; CI checks the BFF's backend routes against FastAPI's live `/openapi.json`. Phase 2: one request per worker screen (`/api/screens/worker-work`, `/api/screens/worker-home`); mobile "My work" went from three sequential requests to one. | WEB-001 | - |
| **WEB-008** | `DONE` | High | inDrive-style hiring: workers "Accept for $X" in one tap or offer another price; employers see who answered (refreshing every 15 s) and Approve one; workers who haven't answered can't be approved. | WEB-003 | - |
| **WEB-009** | `DONE` | Medium | Worker skills: own skills only, the list hidden until "Add a skill"; free typing ("I fix geysers") matched to skills by everyday keywords. Jobs near you ranked for the worker (closeness, urgency, freshness, a price to accept; answered jobs last) with the reason shown. | WEB-003 | - |
| **WEB-010** | `DONE` | Medium | Add photo offers "Take a photo" (phone camera app; in-app webcam on laptops) or "Choose from gallery", on job posts, "Show your work" and chat. | WEB-004 | - |
| **WEB-011** | `IN_PROGRESS` | High | One account hires and finds work, with a mode switch (issue #9, backend). Until then sign-in says which role a number is registered as instead of silently opening the other side. | WEB-001 | - |
