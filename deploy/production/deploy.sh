#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PRODUCTION_DIR="$ROOT_DIR/deploy/production"

: "${MARICHO_VPS:?Set MARICHO_VPS, for example deployer@example-vps}"
: "${MARICHO_DOMAIN:?Set MARICHO_DOMAIN to the public frontend hostname}"
: "${MARICHO_WS_URL:?Set MARICHO_WS_URL to the public websocket URL}"
MARICHO_REMOTE_DIR="${MARICHO_REMOTE_DIR:-apps/maricho}"
MARICHO_IMAGE_TAG="${MARICHO_IMAGE_TAG:-$(git -C "$ROOT_DIR" rev-parse --short=12 HEAD)}"
MARICHO_PUBLIC_URL="${MARICHO_PUBLIC_URL:-https://$MARICHO_DOMAIN}"

export MARICHO_VPS MARICHO_REMOTE_DIR
source "$PRODUCTION_DIR/deploy_upload.sh"

BACKEND_IMAGE="maricho-backend:$MARICHO_IMAGE_TAG"
FRONTEND_IMAGE="maricho-frontend:$MARICHO_IMAGE_TAG"

echo "=================================================="
echo "Building Docker images for $MARICHO_IMAGE_TAG"
echo "=================================================="
docker build -t "$BACKEND_IMAGE" "$ROOT_DIR/backend"
docker build -f "$ROOT_DIR/frontend/Dockerfile" -t "$FRONTEND_IMAGE" \
    --build-arg NEXT_PUBLIC_WS_URL="$MARICHO_WS_URL" "$ROOT_DIR/frontend"

echo "=================================================="
echo "Uploading Docker images"
echo "=================================================="
retry remote "mkdir -p '$MARICHO_REMOTE_DIR'"
upload_image "$BACKEND_IMAGE"
upload_image "$FRONTEND_IMAGE"

echo "=================================================="
echo "Uploading production Compose configuration"
echo "=================================================="
retry push_file "$PRODUCTION_DIR/docker-compose.yml" "$MARICHO_REMOTE_DIR/docker-compose.yml"

echo "=================================================="
echo "Deploying on $MARICHO_VPS"
echo "=================================================="

ssh "${SSH_OPTS[@]}" "$MARICHO_VPS" \
    "IMAGE_TAG=$(printf '%q' "$MARICHO_IMAGE_TAG") REMOTE_DIR=$(printf '%q' "$MARICHO_REMOTE_DIR") bash -s" <<'EOF'
set -euo pipefail

cd "$REMOTE_DIR"
test -f .env

for key in POSTGRES_DB POSTGRES_USER POSTGRES_PASSWORD SECRET_KEY; do
    value="$(grep -E "^${key}=" .env | tail -n 1 | cut -d= -f2- || true)"
    test -n "$value"
    case "$value" in
        replace-with-*|dev-only-*|changeme|password) echo "Invalid placeholder for $key" >&2; exit 1 ;;
    esac
done

export APP_VERSION="$IMAGE_TAG"
docker compose --env-file .env config --quiet

docker compose down --remove-orphans
if ! docker network inspect proxy-tier >/dev/null 2>&1; then
    docker network create proxy-tier
fi
docker compose up -d --no-build

db_ready=false
for _ in $(seq 1 30); do
    if docker compose exec -T db sh -c 'pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB"' >/dev/null 2>&1; then
        db_ready=true
        break
    fi
    sleep 2
done
test "$db_ready" = true

api_ready=false
for _ in $(seq 1 30); do
    if docker compose exec -T api python -c \
        "import urllib.request; urllib.request.urlopen('http://localhost:8000/health/ready')" \
        >/dev/null 2>&1; then
        api_ready=true
        break
    fi
    sleep 2
done
test "$api_ready" = true

current_revision="$(docker compose exec -T api alembic current)"
heads_revision="$(docker compose exec -T api alembic heads)"
grep -q '(head)' <<< "$current_revision"
grep -q 'head' <<< "$heads_revision"
echo "$current_revision"
docker compose exec -T frontend node -e \
    "fetch('http://localhost:3000/').then(r => { if (!r.ok) process.exit(1) }, () => process.exit(1))"

api_container="$(docker compose ps -q api)"
frontend_container="$(docker compose ps -q frontend)"
test "$(docker inspect --format '{{.Config.Image}}' "$api_container")" = "maricho-backend:$IMAGE_TAG"
test "$(docker inspect --format '{{.Config.Image}}' "$frontend_container")" = "maricho-frontend:$IMAGE_TAG"

docker compose ps
docker compose logs api --tail=20
EOF

echo "=================================================="
echo "Public frontend smoke check"
echo "=================================================="
curl --fail --silent --show-error --location "$MARICHO_PUBLIC_URL/" >/dev/null

echo "Deployment completed successfully: $MARICHO_IMAGE_TAG"
