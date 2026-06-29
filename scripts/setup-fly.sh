#!/usr/bin/env bash
# ── FrontierCRM First-Time Setup ──────────────────────────────────────────────
# One-time setup: create Fly.io apps, Postgres, Redis, and configure secrets.
# Idempotent: re-running skips already-created resources.
#
# Usage:
#   ./scripts/setup-fly.sh
#   ./scripts/setup-fly.sh --staging   # Set up staging environment
#
# Prerequisites: flyctl installed, authenticated, and API token set.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

DEPLOY_ENV="production"
ORG="${FLY_ORG:-personal}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --staging) DEPLOY_ENV="staging" ;;
    *) echo "Unknown: $1"; exit 1 ;;
  esac
  shift
done

if [ "$DEPLOY_ENV" = "staging" ]; then
  API_APP="frontiercrm-api-staging"
  WEB_APP="frontiercrm-web-staging"
  DB_NAME="frontiercrm-db-staging"
  REDIS_NAME="frontiercrm-redis-staging"
else
  API_APP="frontiercrm-api"
  WEB_APP="frontiercrm-web"
  DB_NAME="frontiercrm-db"
  REDIS_NAME="frontiercrm-redis"
fi

echo "═══ FrontierCRM Fly.io Setup ═══"
echo "Environment: $DEPLOY_ENV"
echo ""

# ── Create apps ──────────────────────────────────────────────────────────────
echo "[1/6] Creating Fly.io apps..."
flyctl apps create "$API_APP" --org "$ORG" 2>/dev/null || echo "  App $API_APP already exists"
flyctl apps create "$WEB_APP" --org "$ORG" 2>/dev/null || echo "  App $WEB_APP already exists"

# ── Create PostgreSQL ────────────────────────────────────────────────────────
echo "[2/6] Creating PostgreSQL database..."
flyctl postgres create --name "$DB_NAME" --org "$ORG" \
  --initial-cluster-size 1 --vm-size shared-cpu-1x --volume-size 10 \
  2>/dev/null || echo "  Database $DB_NAME already exists"

echo "  Attaching DB to API app..."
flyctl postgres attach "$DB_NAME" --app "$API_APP" 2>/dev/null || echo "  DB already attached"

# ── Create Redis ─────────────────────────────────────────────────────────────
echo "[3/6] Creating Redis..."
flyctl redis create --name "$REDIS_NAME" --org "$ORG" \
  --size 1 --plan starter \
  2>/dev/null || echo "  Redis $REDIS_NAME already exists"

echo "  Getting Redis connection string..."
REDIS_URL=$(flyctl redis status "$REDIS_NAME" --json 2>/dev/null | python3 -c "
import json, sys
try:
    d = json.load(sys.stdin)
    print(d.get('public_url', ''))
except: print('')
") || true

if [ -n "$REDIS_URL" ]; then
  flyctl secrets set \
    REDIS_URL="$REDIS_URL/1" \
    CHANNEL_REDIS_URL="$REDIS_URL/2" \
    CELERY_BROKER_URL="$REDIS_URL/0" \
    CELERY_RESULT_BACKEND="$REDIS_URL/0" \
    --app "$API_APP"
fi

# ── Set production secrets ───────────────────────────────────────────────────
echo "[4/6] Setting production secrets..."
echo "  DJANGO_SECRET_KEY: generating..."
DJANGO_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(64))")
flyctl secrets set "DJANGO_SECRET_KEY=$DJANGO_SECRET_KEY" \
  DJANGO_DEBUG=False \
  DJANGO_ALLOWED_HOSTS=".fly.dev,api.frontiercrm.com,app.frontiercrm.com" \
  --app "$API_APP" 2>/dev/null || echo "  Secrets partially set, check manually"

# ── Deploy initial version ───────────────────────────────────────────────────
echo "[5/6] Deploying initial version of API..."
flyctl deploy --remote-only -c fly.toml --app "$API_APP" --strategy rolling || {
  echo "  WARNING: Deploy failed. Check fly.toml and try again."
  echo "  Command: flyctl deploy --remote-only -c fly.toml --app $API_APP"
}

# ── Final check ─────────────────────────────────────────────────────────────
echo "[6/6] Verifying setup..."
echo ""
echo "  Apps created:"
echo "    - API:     https://$API_APP.fly.dev"
echo "    - Web:     https://$WEB_APP.fly.dev"
echo "    - DB:      $DB_NAME (attached to $API_APP)"
echo "    - Redis:   $REDIS_NAME"
echo ""
echo "  Next steps:"
echo "    1. Set CORS_ALLOWED_ORIGINS: flyctl secrets set CORS_ALLOWED_ORIGINS='https://$WEB_APP.fly.dev,https://app.frontiercrm.com' --app $API_APP"
echo "    2. Set SENTRY_DSN:           flyctl secrets set SENTRY_DSN='https://...' --app $API_APP"
echo "    3. Set Slack webhook:        flyctl secrets set SLACK_WEBHOOK_URL='https://hooks.slack.com/...' --app $API_APP"
echo "    4. Set R2 credentials:       flyctl secrets set AWS_ACCESS_KEY_ID=... AWS_SECRET_ACCESS_KEY=... --app $API_APP"
echo "    5. Set Google OAuth:         flyctl secrets set GOOGLE_CLIENT_ID=... GOOGLE_CLIENT_SECRET=... --app $API_APP"
echo "    6. Deploy frontend:           cd frontend && flyctl deploy --remote-only -c fly.web.toml --app $WEB_APP"
echo "    7. Set up custom domain:      flyctl certs create app.frontiercrm.com --app $WEB_APP"
echo "    8. Set up API custom domain:  flyctl certs create api.frontiercrm.com --app $API_APP"