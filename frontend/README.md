# Maricho frontend (PWA)

The web client for Maricho, built to the approved app UI in [`/wireframes`](../wireframes).
Next.js 16 (App Router) · React 19 · TypeScript (strict) · TanStack Query · zod.
Conventions follow the ECC React / TypeScript / web rules.

## Run it

```bash
cp .env.example .env.local      # BACKEND_URL defaults to http://127.0.0.1:8000
npm install
npm run dev                     # http://localhost:3000
```

The backend must be running (see [`/backend`](../backend)):

```bash
cd ../backend && docker compose up -d --build     # project is named "maricho" in the file
# If 5432/6379 are taken on your machine, move the host ports (the API doesn't need them):
MARICHO_DB_PORT=15433 MARICHO_REDIS_PORT=16380 docker compose up -d --build
```

Use `127.0.0.1`, not `localhost`, in `BACKEND_URL`: Node can resolve `localhost` to `::1`,
which Docker Desktop's port forwarding doesn't answer.

## Checks

```bash
npm run format:check && npm run lint && npm run typecheck && npm test && npm run build
```

### End-to-end (Playwright, needs Docker)

```bash
npx playwright install chromium   # once

npm run test:e2e             # one job, posted → paid, against a real backend
npm run test:visual          # screenshots of the 14 designed screens
npm run test:visual:update   # accept intended UI changes as the new baselines
```

- **Lifecycle** (`e2e/lifecycle/`): a worker and a buyer in two browsers sign up, post, offer,
  hire, chat over the live socket, price on site, review and sign off. `test:e2e` starts its own
  docker-compose project (`maricho-e2e`, API on port 18000) with an empty database and deletes
  it afterwards, so your dev stack and data are untouched. `KEEP_E2E_STACK=1` keeps it running.
- **Visual** (`e2e/visual/`): every `/api/*` call is answered from fixed fixtures at a fixed
  time, so a screenshot changes only when the UI does. It runs inside the
  `mcr.microsoft.com/playwright` Linux image (same as CI) because fonts render differently on
  Windows and macOS. Baselines live in `e2e/visual/__screenshots__/`; review the diff images
  before running `test:visual:update`.
- **Flows** (`e2e/flows/`): sign-in codes and photo uploads in a real browser against the
  stubbed contract from issues #1 and #5, including the on-phone photo shrinking.
  `npx playwright test --project=flows` (no Docker needed).
- CI: `.github/workflows/frontend-e2e.yml` runs both on frontend and backend changes and
  uploads the report (traces, screenshot diffs) when something fails.

## How it fits together

```
browser ────/api/*──┐
                    ├─▶ Next.js route handlers (the BFF) ──Bearer JWT──▶ FastAPI
mobile app ─/api/*──┘     web: JWT in an httpOnly cookie, never in page JS
                          app: JWT returned at sign-in, sent as Authorization: Bearer
browser / app ──ws──▶ FastAPI /jobs/{id}/ws   (chat push; can't go through route handlers)
```

This server is the **one backend-for-frontend for both the website and the mobile app**
([ADR-009](../docs/architecture/adr/009-single-bff-for-web-and-mobile.md)). It owns the client
contract; every FastAPI address it depends on is listed in `src/server/backend-routes.ts`. When
the backend renames something, change that file, not the apps. The lifecycle E2E job checks
the list against the running backend's `/openapi.json`, so drift fails CI.

The mobile app signs in through the same `POST /api/session` with `X-Maricho-Client: mobile`
and gets `{ user, access_token }` back instead of a cookie.

| Path                 | What lives there                                                                          |
| -------------------- | ----------------------------------------------------------------------------------------- |
| `src/app/`           | Routes only — thin pages that hand params to feature screens                              |
| `src/app/api/`       | BFF: `[...path]` proxy, `session` (+ `/code`), `media` upload                             |
| `src/server/`        | BFF internals: `backend-routes.ts` (the FastAPI contract), auth, sign-in-code rules       |
| `src/core/api/`      | `http.ts` fetch wrapper, `schemas.ts` zod contracts, `endpoints.ts`                       |
| `src/core/query/`    | Query client, keys, offline persistence and mutation replay                               |
| `src/core/session/`  | Session context and the on-device profile (name, radius, availability)                    |
| `src/components/ui/` | Design-system components; styles in `src/styles/` (tokens → components)                   |
| `src/features/*`     | Screens and their hooks: `accounts`, `employer`, `jobs`, `worker`, `workers`, `messaging` |

### Offline-first

- Reads are served from the on-device cache first (`networkMode: "offlineFirst"`), and the
  cache is persisted to `localStorage` for 7 days.
- Writes made offline (post a job, send an offer, chat message, quote, sign-off, …) are
  paused, persisted, and replayed on reconnect or next launch. The banner shows how many are
  waiting.
- `public/sw.js` caches the app shell and static assets (production builds only).

### Gaps against the design (backend not there yet)

- **No names:** the backend stores phone numbers only, so the display name is kept on the
  device and workers are introduced by grade and trade ("Expert plumber").
- **Trades:** the backend has six trades; other skills in the picker are marked _soon_.
- **Sign-in code (WEB-005):** built, waiting on the backend ([#5]). `/api/session/code` asks
  `/auth/otp/request`; while that is 404, sign-up skips the code step and uses the `/token` mock.
- **Photos and voice notes (WEB-004):** built, waiting on the backend ([#1]). The app checks
  `GET /media` (404 = not yet); until then photos stay on the phone and chat hides the
  camera/mic. When it's on, photos are shrunk to ≤1280 px JPEG (GPS stripped) before upload, and
  uploaded photos only download when tapped.
- **No ratings endpoint:** the star rating and tags are written into the job's sign-off
  record (`client_words`).
- **Job timing** ("Today", "This week") is carried as a `Needed:` line in the description.

See WEB-004 – WEB-006 in [`docs/backlog.md`](../docs/backlog.md).

[#1]: https://github.com/Rest-creator/MARITCHO/issues/1
[#5]: https://github.com/Rest-creator/MARITCHO/issues/5
