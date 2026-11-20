# Production VPS Deployment

This deployment clones (or fetches) the repository directly onto the VPS at
the requested ref, builds the version-tagged Docker images there with
`docker compose build`, takes an automated pre-migration PostgreSQL backup,
and rolls out the production Compose stack with health, Alembic head, and
`pgvector` verification. Nothing is built or uploaded from the machine
running `deploy.sh` — it only drives the build and rollout over SSH, so
deploy speed depends on the VPS's own build time, not your local upload
bandwidth.

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
This `.env` lives outside the git clone (`~/apps/maricho/.env`, not
`~/apps/maricho/repo/.env`) and survives every deploy.

The VPS deploy user needs `git` installed and network access to clone the
repository (public, or with deploy keys/credentials configured for a
private repo — `deploy.sh` passes whatever `git remote get-url origin`
resolves to locally, so a private repo needs the VPS's own git credentials
set up for that URL).

## Deploy

From the repository root:

```bash
deploy/production/deploy.sh
```

Defaults to the production VPS (`MARICHO_VPS=restk-vps`, `MARICHO_DOMAIN=maricho.restk.tech`,
`MARICHO_WS_URL=wss://maricho.restk.tech`). `restk-vps` is an SSH config alias
(`~/.ssh/config`); add it there before deploying from a new machine. Override
any of the three for a different target:

```bash
export MARICHO_VPS=deployer@example-vps
export MARICHO_DOMAIN=example.com
export MARICHO_WS_URL=wss://example.com
deploy/production/deploy.sh
```

This fetches and checks out the current local `HEAD` commit on the VPS (via
`git fetch --depth 1 origin <sha>`, so the VPS always builds exactly the
commit you're deploying from, not just whatever is on a branch), builds the
`api`/`frontend` images there with `docker compose build`, and rolls out.

Optional values:

```bash
export MARICHO_REMOTE_DIR=/home/deployer/apps/maricho
export MARICHO_GIT_URL=git@github.com:Org/MARITCHO.git   # defaults to the local `origin` remote
export MARICHO_GIT_REF="$(git rev-parse HEAD)"            # any ref git fetch accepts: a SHA, tag, or branch
export MARICHO_IMAGE_TAG="$(git rev-parse --short=12 HEAD)"
export MARICHO_PUBLIC_URL=https://maricho.restk.tech
```

### Central Caddy (`Caddyfile.maricho`)

The repo clone on the VPS (`~/apps/maricho/repo/deploy/production/Caddyfile.maricho`)
always has the current version after a deploy. Merging it into the VPS's
central Caddyfile and reloading `caddy-proxy` is a separate, manual step —
`deploy.sh` does not touch the central Caddy config:

```bash
ssh deployer@vps
cp ~/core/Caddyfile ~/core/Caddyfile.maricho-backup-"$(date -u +%Y%m%dT%H%M%SZ)"
# merge apps/maricho/repo/deploy/production/Caddyfile.maricho's `maricho.restk.tech { ... }`
# block into ~/core/Caddyfile, then validate before reloading:
docker exec caddy-proxy caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile
docker exec caddy-proxy caddy reload --config /etc/caddy/Caddyfile --adapter caddyfile
```

## Pre-deploy Backups & Rollback

- Before every deployment, `deploy.sh` writes a compressed snapshot to
  `~/apps/maricho/backups/pre-deploy-<tag>-<timestamp>.sql.gz` (retaining the 5
  most recent backups).
- To roll back the application containers, set `MARICHO_IMAGE_TAG` to the
  previous commit tag and re-run `deploy/production/deploy.sh`.
