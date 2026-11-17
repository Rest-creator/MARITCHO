# Production VPS Deployment

This deployment builds version-tagged Docker images locally, uploads them to the
VPS in resumable compressed chunks (`deploy_upload.sh`), takes an automated
pre-migration PostgreSQL backup, and rolls out the production Compose stack with
health, Alembic head, and `pgvector` verification.

## Architecture & Security

- **PostgreSQL 16 + `pgvector` (`pgvector/pgvector:0.7.4-pg16`):** Powers
  transactional storage and HNSW cosine semantic search (`jobs.problem_embedding`).
- **Redis 7 (`redis:7-alpine`):** Bounded LRU cache + append-only persistence
  for live WebSocket pub/sub and rate limiting.
- **FastAPI Backend (`maricho-api`):** Runs as non-root `app` (`uid 1000`),
  executes `alembic upgrade head` on startup, and serves REST + `/jobs/*/ws`
  WebSockets with `--proxy-headers`.
- **Next.js 16 BFF & PWA (`maricho-frontend`):** Standalone Node 22 server
  running as non-root `nextjs` (`uid 1001`), owning the unified client contract
  for web and mobile (`ADR-009`).
- **Central Caddy Reverse Proxy (`Caddyfile.maricho`):** Terminates TLS 1.2/1.3
  using **ECC (`key_type p256` / ECDSA P-256)** certificates for faster handshakes
  on low-end Android phones, proxies `/jobs/*/ws` + `/health/*` to
  `maricho-api:8000`, and routes all web + `/api/*` BFF requests to
  `maricho-frontend:3000` over the `proxy-tier` network.

## One-time VPS setup

Create the deployment directory and the external proxy network as the SSH
deployment user:

```bash
mkdir -p ~/apps/maricho ~/apps/maricho/backups
docker network inspect proxy-tier >/dev/null 2>&1 || docker network create proxy-tier
```

Copy `.env.example` to `~/apps/maricho/.env`, replace every placeholder, and
set the production domain/websocket values. Do not commit the real `.env`.

## Deploy

From the repository root:

```bash
export MARICHO_VPS=deployer@example-vps
export MARICHO_DOMAIN=maricho.restk.tech
export MARICHO_WS_URL=wss://maricho.restk.tech
deploy/production/deploy.sh
```

Optional values:

```bash
export MARICHO_REMOTE_DIR=/home/deployer/apps/maricho
export MARICHO_IMAGE_TAG="$(git rev-parse --short=12 HEAD)"
export MARICHO_PUBLIC_URL=https://maricho.restk.tech
```

### Central Caddy (`Caddyfile.maricho`)

Include or merge `deploy/production/Caddyfile.maricho` into the VPS central
Caddyfile (`/home/winstontino/core/Caddyfile`) and restart `caddy-proxy`:

```bash
scp deploy/production/Caddyfile.maricho deployer@vps:/home/winstontino/core/Caddyfile.maricho
ssh deployer@vps docker restart caddy-proxy
```

## Pre-deploy Backups & Rollback

- Before every deployment, `deploy.sh` writes a compressed snapshot to
  `~/apps/maricho/backups/pre-deploy-<tag>-<timestamp>.sql.gz` (retaining the 5
  most recent backups).
- To roll back the application containers, set `MARICHO_IMAGE_TAG` to the
  previous commit tag and re-run `deploy/production/deploy.sh`.
