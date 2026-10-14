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
npm run test:visual          # screenshots of the 13 designed screens
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
- CI: `.github/workflows/frontend-e2e.yml` runs both on frontend and backend changes and
  uploads the report (traces, screenshot diffs) when something fails.

## How it fits together

```
browser ──/api/*──▶ Next.js route handler (BFF) ──Bearer JWT──▶ FastAPI
   │                     └─ JWT lives in an httpOnly cookie, never in page JS
   └──ws──▶ FastAPI /jobs/{id}/ws   (chat push; token fetched from /api/session/socket-token)
```

| Path                 | What lives there                                                                          |
| -------------------- | ----------------------------------------------------------------------------------------- |
| `src/app/`           | Routes only — thin pages that hand params to feature screens                              |
| `src/app/api/`       | BFF: `[...path]` proxy (allow-listed roots), `session` sign-in/out                        |
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
- **No OTP:** sign-up skips the 6-digit code step — `/token` is a development mock (BACK-009).
- **No uploads:** photos are previewed on the device but not sent (WEB-004).
- **No ratings endpoint:** the star rating and tags are written into the job's sign-off
  record (`client_words`).
- **Job timing** ("Today", "This week") is carried as a `Needed:` line in the description.

See WEB-004 – WEB-006 in [`docs/backlog.md`](../docs/backlog.md).
