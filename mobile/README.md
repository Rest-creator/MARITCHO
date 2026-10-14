# Maricho mobile (Flutter)

The worker-first Android app: find jobs, offer, get hired, and do the work on site — with or
without signal. Architecture rules live in [`AGENTS.md`](../AGENTS.md) (feature-first folders,
Cubits, `Result` instead of exceptions, explicit types).

## Run it

```bash
flutter pub get
flutter run --dart-define=API_BASE_URL=http://10.0.2.2:3000/api   # emulator → the BFF on your computer
```

The app talks to the **BFF** (the Next.js server's `/api`), not to FastAPI directly
([ADR-009](../docs/architecture/adr/009-single-bff-for-web-and-mobile.md)): start the backend
with docker-compose and the website with `npm run dev` in `frontend/` first. `10.0.2.2` is the
emulator's name for your computer. Sign-in uses the same two steps as the website (ask for a
code, then sign in with it); in development the backend's code is always `123456`.

## Checks

```bash
dart format --set-exit-if-changed lib test
flutter analyze
flutter test
```

No Flutter SDK on your machine? The same commands run in Docker:

```bash
node tool/flutter_in_docker.mjs analyze
node tool/flutter_in_docker.mjs test
node tool/flutter_in_docker.mjs dart format lib test
```

CI runs them on every change to `mobile/` (`.github/workflows/mobile-ci.yml`).

## Working offline (APP-002)

Work a worker does on site is **saved on the phone first** and sent when there is signal:

- **"I've arrived"** on an active job confirms the price on site (labour + materials, pre-filled
  from their offer) → `POST /jobs/{id}/quote`.
- **"Add photo"** takes a camera photo (shrunk to ≤1280 px by the camera plugin), keeps a copy in
  the app's storage, uploads it to `POST /media` and shares it in the job's chat. Until the
  backend has `/media` (issue #1) photos wait on the phone and retry hourly.

How it fits together:

| Piece | Job |
| --- | --- |
| `core/sync/sqlite_outbox.dart` | The queue (`offline_queue` table); survives restarts. |
| `core/sync/sync_service.dart` | Sends what's due. A failure never blocks the rest: each item gets its own retry time (30 s doubling to 15 min). A permanent refusal is kept with the backend's reason and shown on the job, with "Try again". |
| `core/sync/sync_scheduler.dart` | When to send: at start-up, when the app returns to the foreground, every minute while open, and straight after something is queued. |
| `features/jobs/data/repositories/job_work_repository.dart` | What screens call to queue a price or a photo. |

Reads are offline-first too: every list is cached (`cached_responses`) and shown when the
network fails.

## Notes

- Backend `Decimal` fields (money, rates, coordinates) arrive as JSON strings like `"40.00"`;
  models read them with `core/json/json_number.dart`.
- Release builds declare `INTERNET` in `android/app/src/main/AndroidManifest.xml` (Flutter only
  adds it to debug builds).
