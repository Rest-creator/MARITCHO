# VPS deployment

This deployment follows the ProjectFlow pattern: build tagged images locally,
upload them to the VPS in resumable compressed chunks, then start the remote
production Compose stack from those exact images.

## One-time VPS setup

Create the deployment directory and the external proxy network as the SSH
deployment user:

```bash
mkdir -p ~/apps/maricho
docker network inspect proxy-tier >/dev/null 2>&1 || docker network create proxy-tier
```

Copy `.env.example` to `~/apps/maricho/.env`, replace every placeholder, and
set the production domain/websocket values. Do not commit the real `.env`.
The VPS must have Docker Engine, Docker Compose v2, `curl`, `ssh`, and `scp`.
The SSH user must be allowed to run Docker.

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

### Central Caddy

The VPS terminates TLS and routes `maricho.restk.tech` through the shared
reverse proxy (`caddy-proxy`, config at `/home/winstontino/core/Caddyfile` on
the VPS, source of truth in
`TESE-MARKET---BFF-ARCHITECTURE/infrastructure/caddy/Caddyfile`), not a
per-project Caddy instance. It proxies straight to `maricho-frontend:3000` on
the shared `proxy-tier` network — the Next.js BFF serves the web app, the
mobile API, and the websocket upgrade from that single origin, so no
per-service subdomain is needed. After editing that Caddyfile, upload it and
restart the shared proxy container (a `reload` is not enough across a
bind-mount):

```bash
scp TESE-MARKET---BFF-ARCHITECTURE/infrastructure/caddy/Caddyfile \
    deployer@vps:/home/winstontino/core/Caddyfile
ssh deployer@vps docker restart caddy-proxy
```

The script fails before traffic if the remote `.env` is missing or contains
known placeholders. It verifies Compose configuration, database readiness,
API dependency readiness, Alembic's current revision, frontend rendering,
exact running image tags, and the public frontend URL.

## Rollback

Keep the previous image tag and set `MARICHO_IMAGE_TAG` to it before rerunning
the deployment. The VPS retains the uploaded Docker image unless it has been
explicitly pruned.
