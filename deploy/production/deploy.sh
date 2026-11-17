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

SSH_OPTS=(-o ServerAliveInterval=15 -o ServerAliveCountMax=8 -o ConnectTimeout=20)

echo "=================================================="
echo "Deploying $MARICHO_GIT_REF (tag $MARICHO_IMAGE_TAG) on $MARICHO_VPS"
echo "Pulling from $MARICHO_GIT_URL and building on the VPS"
echo "=================================================="

ssh "${SSH_OPTS[@]}" "$MARICHO_VPS" \
    "GIT_URL=$(printf '%q' "$MARICHO_GIT_URL") GIT_REF=$(printf '%q' "$MARICHO_GIT_REF") IMAGE_TAG=$(printf '%q' "$MARICHO_IMAGE_TAG") REMOTE_DIR=$(printf '%q' "$MARICHO_REMOTE_DIR") WS_URL=$(printf '%q' "$MARICHO_WS_URL") bash -s" <<'EOF'
set -euo pipefail

mkdir -p "$REMOTE_DIR" "$REMOTE_DIR/backups"
REMOTE_DIR="$(cd "$REMOTE_DIR" && pwd)"
cd "$REMOTE_DIR"
test -f .env

for key in POSTGRES_DB POSTGRES_USER POSTGRES_PASSWORD SECRET_KEY; do
    value="$(grep -E "^${key}=" .env | tail -n 1 | cut -d= -f2- || true)"
    test -n "$value"
    case "$value" in
        replace-with-*|dev-only-*|changeme|password) echo "Invalid placeholder for $key" >&2; exit 1 ;;
    esac
done

echo "=================================================="
echo "Fetching $GIT_REF"
echo "=================================================="
if [ ! -d repo/.git ]; then
    git clone "$GIT_URL" repo
fi
git -C repo fetch --depth 1 origin "$GIT_REF"
git -C repo checkout --detach FETCH_HEAD
git -C repo clean -fdx

cd repo/deploy/production
export APP_VERSION="$IMAGE_TAG"
export NEXT_PUBLIC_WS_URL="$WS_URL"
COMPOSE=(docker compose --env-file "$REMOTE_DIR/.env")

"${COMPOSE[@]}" config --quiet

echo "=================================================="
echo "Building images on the VPS"
echo "=================================================="
"${COMPOSE[@]}" build api frontend

if ! docker network inspect proxy-tier >/dev/null 2>&1; then
    docker network create proxy-tier
fi

# Take a pre-migration database backup when an existing db container is running.
if [ -n "$("${COMPOSE[@]}" ps -q db 2>/dev/null || true)" ]; then
    if "${COMPOSE[@]}" exec -T db sh -c 'pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB"' >/dev/null 2>&1; then
        backup_file="$REMOTE_DIR/backups/pre-deploy-${IMAGE_TAG}-$(date -u +%Y%m%dT%H%M%SZ).sql.gz"
        echo "Creating pre-deploy database snapshot: $backup_file"
        "${COMPOSE[@]}" exec -T db sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB"' | gzip -9 > "$backup_file"
        ls -1t "$REMOTE_DIR"/backups/pre-deploy-*.sql.gz 2>/dev/null | tail -n +6 | xargs -r rm -f
    fi
fi

# Rolling update: start stateful services first, then roll api + frontend without full downtime.
"${COMPOSE[@]}" up -d --no-build db redis

db_ready=false
for _ in $(seq 1 30); do
    if "${COMPOSE[@]}" exec -T db sh -c 'pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB"' >/dev/null 2>&1; then
        db_ready=true
        break
    fi
    sleep 2
done
test "$db_ready" = true

"${COMPOSE[@]}" up -d --no-build --remove-orphans api frontend

api_ready=false
for _ in $(seq 1 30); do
    if "${COMPOSE[@]}" exec -T api python -c \
        "import urllib.request; urllib.request.urlopen('http://localhost:8000/health/ready')" \
        >/dev/null 2>&1; then
        api_ready=true
        break
    fi
    sleep 2
done
test "$api_ready" = true

current_revision="$("${COMPOSE[@]}" exec -T api alembic current)"
heads_revision="$("${COMPOSE[@]}" exec -T api alembic heads)"
grep -q '(head)' <<< "$current_revision"
grep -q 'head' <<< "$heads_revision"
echo "$current_revision"

# Verify pgvector extension is active in PostgreSQL.
"${COMPOSE[@]}" exec -T db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -tAc "SELECT 1 FROM pg_extension WHERE extname = '\''vector'\''"' | grep -q '1'

"${COMPOSE[@]}" exec -T frontend node -e \
    "fetch('http://localhost:3000/').then(r => { if (!r.ok) process.exit(1) }, () => process.exit(1))"

api_container="$("${COMPOSE[@]}" ps -q api)"
frontend_container="$("${COMPOSE[@]}" ps -q frontend)"
test "$(docker inspect --format '{{.Config.Image}}' "$api_container")" = "maricho-backend:$IMAGE_TAG"
test "$(docker inspect --format '{{.Config.Image}}' "$frontend_container")" = "maricho-frontend:$IMAGE_TAG"

"${COMPOSE[@]}" ps
"${COMPOSE[@]}" logs api --tail=20
EOF

echo "=================================================="
echo "Public frontend smoke check"
echo "=================================================="
curl --fail --silent --show-error --location "$MARICHO_PUBLIC_URL/" >/dev/null

echo "Deployment completed successfully: $MARICHO_IMAGE_TAG"
