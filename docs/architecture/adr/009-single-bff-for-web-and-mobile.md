# ADR 009: One Backend-for-Frontend for Web and Mobile

## Status
Accepted and implemented (2026-10-15). Phase 1: contract ownership, mobile on the BFF, drift
check. Phase 2: screen endpoints for the worker's "My work" (`/api/screens/worker-work`) and
"Jobs near you" (`/api/screens/worker-home`); more screens follow the same pattern
(`frontend/src/server/screen-bundle.ts`) when they need more than one request.

## Context
Two clients talk to the FastAPI domain API in different ways:

- The Next.js PWA (`frontend/`) goes through its own `/api/*` route handlers, which hold the JWT
  in an httpOnly cookie and otherwise pass requests straight through.
- The Flutter app (`mobile/`) calls FastAPI directly with a bearer token.

The clients and the backend are built by different people, in parallel. On 2026-10-14 the backend
shipped sign-in codes and uploads (PR #8) at addresses that differed from the contract agreed in
issues #1 and #5 (`/otp/*` instead of `/auth/otp/*`, `POST /media/upload` instead of
`POST /media`). Both clients went on running, but quietly kept the features switched off, and
with `APP_ENV=production` the web sign-in would have failed outright. Nothing in CI could notice:
each side's tests used its own idea of the contract.

Earlier the same day the mobile app was found reading every backend `Decimal` as a JSON number
when the API sends strings, so every list with a price failed to load. Same root cause: each
client re-implements its own reading of the domain API.

## Decision
**The Next.js server is the single backend-for-frontend for both clients.** It owns the client
contract; FastAPI stays the domain API behind it.

- **One client contract.** Both apps call `/api/*` on the Next.js origin. Where the BFF's
  contract differs from FastAPI's, the BFF translates, in one place
  (`frontend/src/server/backend-routes.ts`). Backend renames are absorbed there instead of in two
  apps.
- **Two ways to carry the session, same endpoints.** The web app keeps the httpOnly cookie
  (page scripts never see the token). The mobile app signs in through the same `POST /api/session`
  with `X-Maricho-Client: mobile` and gets the token in the response body, then sends it as
  `Authorization: Bearer`. The BFF accepts either.
- **Drift fails CI.** The lifecycle E2E job starts the real backend and checks every route in
  `backend-routes.ts` against FastAPI's live `/openapi.json`.
- **Not through the BFF: live chat.** Next.js route handlers can't relay WebSockets, so both
  clients still open `/jobs/{id}/ws` on FastAPI directly (ADR-008), with a token from
  `/api/session/socket-token` (web) or the stored bearer token (mobile).
- **Phase 2:** screen-shaped endpoints (e.g. the worker's "My work" screen in one request instead
  of three), which matter on pay-as-you-go data bundles. Those belong in the BFF, never in the
  domain API.

## Consequences
- **Positive:** a backend change that breaks the client contract is fixed once, in TypeScript, by
  the people who own the clients, and the drift check makes it visible instead of silent.
- **Positive:** the mobile app gets the web app's already-hardened behaviour for free: request
  timeouts, the upload size cap, cacheable media responses, the sign-in-code fallback.
- **Negative:** one more network hop for mobile (phone → Next.js → FastAPI), and the Next.js
  server becomes required for mobile, not just for the website. In production both run on the
  same host (`deploy/production/docker-compose.yml`), so the hop is local.
- **Negative:** chat remains the exception that talks to FastAPI directly, so FastAPI's
  WebSocket address is still part of what both clients must know.
