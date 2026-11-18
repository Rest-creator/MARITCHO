#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

: "${MARICHO_VPS:?Set MARICHO_VPS, for example deployer@example-vps}"
: "${MARICHO_DOMAIN:?Set MARICHO_DOMAIN to the public frontend hostname}"
: "${MARICHO_WS_URL:?Set MARICHO_WS_URL to the public websocket URL}"
MARICHO_REMOTE_DIR="${MARICHO_REMOTE_DIR:-apps/maricho}"
MARICHO_GIT_URL="${MARICHO_GIT_URL:-$(git -C "$ROOT_DIR" remote get-url origin)}"
MARICHO_GIT_REF="${MARICHO_GIT_REF:-$(git -C "$ROOT_DIR" rev-parse HEAD)}"
MARICHO_IMAGE_TAG="${MARICHO_IMAGE_TAG:-$(git -C "$ROOT_DIR" rev-parse --short=12 "$MARICHO_GIT_REF")}"
MARICHO_PUBLIC_URL="${MARICHO_PUBLIC_URL:-https://$MARICHO_DOMAIN}"

SSH_OPTS=(-o ServerAliveInterval=15 -o ServerAliveCountMax=8 -o ConnectTimeout=20 -o TCPKeepAlive=yes)

# A unique, unguessable sentinel the remote script must print as its literal
# last line. Trusting ssh's bare exit code isn't enough: a run was once
# silently truncated partway through (likely docker compose exec's stdin
# interacting badly with the heredoc/script delivery over a long-lived SSH
# session) while ssh itself still reported success. Requiring this exact
# string turns that failure mode into a loud one instead of a false "deploy
# completed" that leaves production on stale images.
SENTINEL="MARICHO_DEPLOY_OK_$(date +%s)_$$"

REMOTE_SCRIPT="$(mktemp)"
REMOTE_OUTPUT="$(mktemp)"
trap 'rm -f "$REMOTE_SCRIPT" "$REMOTE_OUTPUT"' EXIT

cat > "$REMOTE_SCRIPT" <<SCRIPT
set -euo pipefail

GIT_URL=$(printf '%q' "$MARICHO_GIT_URL")
GIT_REF=$(printf '%q' "$MARICHO_GIT_REF")
IMAGE_TAG=$(printf '%q' "$MARICHO_IMAGE_TAG")
REMOTE_DIR=$(printf '%q' "$MARICHO_REMOTE_DIR")
WS_URL=$(printf '%q' "$MARICHO_WS_URL")

mkdir -p "\$REMOTE_DIR" "\$REMOTE_DIR/backups"
REMOTE_DIR="\$(cd "\$REMOTE_DIR" && pwd)"
cd "\$REMOTE_DIR"
test -f .env

for key in POSTGRES_DB POSTGRES_USER POSTGRES_PASSWORD SECRET_KEY; do
    value="\$(grep -E "^\${key}=" .env | tail -n 1 | cut -d= -f2- || true)"
    test -n "\$value"
    case "\$value" in
        replace-with-*|dev-only-*|changeme|password) echo "Invalid placeholder for \$key" >&2; exit 1 ;;
    esac
done

echo "=================================================="
echo "Fetching \$GIT_REF"
echo "=================================================="
if [ ! -d repo/.git ]; then
    git clone "\$GIT_URL" repo
fi
git -C repo fetch --depth 1 origin "\$GIT_REF"
git -C repo checkout --detach FETCH_HEAD
git -C repo clean -fdx

cd repo/deploy/production
export APP_VERSION="\$IMAGE_TAG"
export NEXT_PUBLIC_WS_URL="\$WS_URL"
COMPOSE=(docker compose --env-file "\$REMOTE_DIR/.env")

"\${COMPOSE[@]}" config --quiet

echo "=================================================="
echo "Building images on the VPS"
echo "=================================================="
"\${COMPOSE[@]}" build api frontend < /dev/null

if ! docker network inspect proxy-tier >/dev/null 2>&1; then
    docker network create proxy-tier
fi

# Take a pre-migration database backup when an existing db container is running.
if [ -n "\$("\${COMPOSE[@]}" ps -q db 2>/dev/null || true)" ]; then
    if "\${COMPOSE[@]}" exec -T db sh -c 'pg_isready -U "\$POSTGRES_USER" -d "\$POSTGRES_DB"' < /dev/null >/dev/null 2>&1; then
        backup_file="\$REMOTE_DIR/backups/pre-deploy-\${IMAGE_TAG}-\$(date -u +%Y%m%dT%H%M%SZ).sql.gz"
        echo "Creating pre-deploy database snapshot: \$backup_file"
        "\${COMPOSE[@]}" exec -T db sh -c 'pg_dump -U "\$POSTGRES_USER" -d "\$POSTGRES_DB"' < /dev/null | gzip -9 > "\$backup_file"
        ls -1t "\$REMOTE_DIR"/backups/pre-deploy-*.sql.gz 2>/dev/null | tail -n +6 | xargs -r rm -f
    fi
fi

echo "=================================================="
echo "Rolling out db/redis"
echo "=================================================="
"\${COMPOSE[@]}" up -d --no-build db redis < /dev/null

db_ready=false
for _ in \$(seq 1 30); do
    if "\${COMPOSE[@]}" exec -T db sh -c 'pg_isready -U "\$POSTGRES_USER" -d "\$POSTGRES_DB"' < /dev/null >/dev/null 2>&1; then
        db_ready=true
        break
    fi
    sleep 2
done
test "\$db_ready" = true
echo "db is ready"

# Photo/voice uploads: the media volume was first created root-owned (before
# the image shipped the directory), while the API runs as the unprivileged
# "app" user, so every upload failed with PermissionError (HTTP 500). Re-own it
# on every deploy (idempotent, cheap) and prove "app" can write before rolling.
# (No backticks in this heredoc: it is unquoted, so they would run locally.)
echo "Ensuring the media volume is writable by the api user"
"\${COMPOSE[@]}" run --rm --no-deps --user 0 --entrypoint sh api -c \\
    'mkdir -p /var/lib/maricho/media && chown -R app:app /var/lib/maricho/media' < /dev/null
"\${COMPOSE[@]}" run --rm --no-deps --entrypoint sh api -c \\
    'probe=/var/lib/maricho/media/.write-probe && touch "\$probe" && rm -f "\$probe"' < /dev/null

echo "=================================================="
echo "Rolling out api/frontend"
echo "=================================================="
"\${COMPOSE[@]}" up -d --no-build --remove-orphans api frontend < /dev/null

api_ready=false
for _ in \$(seq 1 30); do
    if "\${COMPOSE[@]}" exec -T api python -c \\
        "import urllib.request; urllib.request.urlopen('http://localhost:8000/health/ready')" \\
        < /dev/null >/dev/null 2>&1; then
        api_ready=true
        break
    fi
    sleep 2
done
test "\$api_ready" = true
echo "api is ready"

current_revision="\$("\${COMPOSE[@]}" exec -T api alembic current < /dev/null)"
heads_revision="\$("\${COMPOSE[@]}" exec -T api alembic heads < /dev/null)"
grep -q '(head)' <<< "\$current_revision"
grep -q 'head' <<< "\$heads_revision"
echo "alembic: \$current_revision"

# Verify pgvector extension is active in PostgreSQL.
"\${COMPOSE[@]}" exec -T db sh -c 'psql -U "\$POSTGRES_USER" -d "\$POSTGRES_DB" -tAc "SELECT 1 FROM pg_extension WHERE extname = '"'"'vector'"'"'"' < /dev/null | grep -q '1'
echo "pgvector: active"

"\${COMPOSE[@]}" exec -T frontend node -e \\
    "fetch('http://localhost:3000/').then(r => { if (!r.ok) process.exit(1) }, () => process.exit(1))" < /dev/null
echo "frontend: internal check ok"

api_container="\$("\${COMPOSE[@]}" ps -q api)"
frontend_container="\$("\${COMPOSE[@]}" ps -q frontend)"
test "\$(docker inspect --format '{{.Config.Image}}' "\$api_container")" = "maricho-backend:\$IMAGE_TAG"
test "\$(docker inspect --format '{{.Config.Image}}' "\$frontend_container")" = "maricho-frontend:\$IMAGE_TAG"
echo "image tags: confirmed \$IMAGE_TAG"

"\${COMPOSE[@]}" ps
"\${COMPOSE[@]}" logs api --tail=20

echo "$SENTINEL"
SCRIPT

echo "=================================================="
echo "Deploying $MARICHO_GIT_REF (tag $MARICHO_IMAGE_TAG) on $MARICHO_VPS"
echo "Pulling from $MARICHO_GIT_URL and building on the VPS"
echo "=================================================="

# Deliver the script via scp and execute it from a file, rather than piping
# it over the same SSH session's stdin (the heredoc approach this replaced):
# a long-running remote script that itself runs commands attached to stdin
# (docker compose exec without an explicit `< /dev/null`, in particular) can
# interact badly with a stdin that is also mid-delivery of the controlling
# script, truncating it silently. Decoupling script delivery from execution,
# and redirecting every exec's stdin from /dev/null, removes that risk
# entirely rather than guessing at the exact mechanism.
scp "${SSH_OPTS[@]}" -q "$REMOTE_SCRIPT" "$MARICHO_VPS:/tmp/maricho-deploy-$$.sh"
ssh "${SSH_OPTS[@]}" "$MARICHO_VPS" \
    "bash /tmp/maricho-deploy-$$.sh; rc=\$?; rm -f /tmp/maricho-deploy-$$.sh; exit \$rc" \
    | tee "$REMOTE_OUTPUT"

if ! grep -qF "$SENTINEL" "$REMOTE_OUTPUT"; then
    echo "FATAL: remote deploy script did not reach its completion sentinel." >&2
    echo "The run likely stopped partway through without ssh reporting a failure." >&2
    exit 1
fi

echo "=================================================="
echo "Public frontend smoke check"
echo "=================================================="
curl --fail --silent --show-error --location "$MARICHO_PUBLIC_URL/" >/dev/null

echo "Deployment completed successfully: $MARICHO_IMAGE_TAG"
