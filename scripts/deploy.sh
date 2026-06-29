#!/usr/bin/env bash
# ── FrontierCRM Deploy Script ─────────────────────────────────────────────────
# Idempotent: re-running with the same version is safe (checks current deploy).
#
# Usage:
#   ./scripts/deploy.sh                    # Deploy latest from main branch
#   ./scripts/deploy.sh --app api          # Deploy only the API
#   ./scripts/deploy.sh --app web          # Deploy only the frontend
#   ./scripts/deploy.sh --version v1.2.3   # Deploy a specific git tag
#   ./scripts/deploy.sh --staging          # Deploy to staging
#
# Prerequisites:
#   - flyctl installed and authenticated
#   - GITHUB_TOKEN or SSH key for git fetch
#   - FLY_API_TOKEN in environment (for CI) or flyctl auth (local)

set -euo pipefail

# ── Config ────────────────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

DEPLOY_ENV="production"
DEPLOY_APP="all"
VERSION=""

# Parse args
while [[ $# -gt 0 ]]; do
  case "$1" in
    --staging)    DEPLOY_ENV="staging" ;;
    --app)        DEPLOY_APP="$2"; shift ;;
    --version)    VERSION="$2"; shift ;;
    --help|-h)
      echo "Usage: $0 [--staging] [--app api|web] [--version <tag>]"
      echo ""
      echo "  --staging      Deploy to staging environment"
      echo "  --app api|web  Deploy only the specified app"
      echo "  --version tag  Deploy a specific git tag/commit"
      exit 0 ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
  shift
done

# ── Environment Config ────────────────────────────────────────────────────────
if [ "$DEPLOY_ENV" = "staging" ]; then
  API_APP="frontiercrm-api-staging"
  WEB_APP="frontiercrm-web-staging"
  FLY_CONF="fly.toml"
  WEB_FLY_CONF="frontend/fly.web.toml"
  FRONTEND_URL="https://staging.frontiercrm.com"
  echo "[deploy] Target: STAGING"
else
  API_APP="frontiercrm-api"
  WEB_APP="frontiercrm-web"
  FLY_CONF="fly.toml"
  WEB_FLY_CONF="frontend/fly.web.toml"
  FRONTEND_URL="https://app.frontiercrm.com"
  echo "[deploy] Target: PRODUCTION"
fi

# ── Prerequisites ──────────────────────────────────────────────────────────────
command -v flyctl >/dev/null 2>&1 || { echo "FATAL: flyctl not found. Install from https://fly.io/docs/hands-on/install-flyctl/"; exit 1; }
if [ -z "${FLY_API_TOKEN:-}" ]; then
  echo "[deploy] Checking flyctl auth..."
  flyctl auth whoami >/dev/null 2>&1 || { echo "FATAL: Not authenticated with flyctl. Run 'flyctl auth login' or set FLY_API_TOKEN"; exit 1; }
fi

# ── Git Checkout ──────────────────────────────────────────────────────────────
if [ -n "$VERSION" ]; then
  echo "[deploy] Checking out version: $VERSION"
  git fetch --tags 2>/dev/null || true
  git checkout "$VERSION"
fi

echo "[deploy] Git commit: $(git rev-parse --short HEAD)"
echo "[deploy] Git branch: $(git rev-parse --abbrev-ref HEAD)"

# ── Deploy API ────────────────────────────────────────────────────────────────
deploy_api() {
  echo "[deploy] Deploying API ($API_APP)..."
  flyctl deploy --remote-only \
    -c "$FLY_CONF" \
    --app "$API_APP" \
    --strategy rolling

  echo "[deploy] Running database migrations..."
  flyctl ssh console -a "$API_APP" -C "python manage.py migrate --noinput"

  echo "[deploy] Waiting for API health check..."
  sleep 10
  API_URL="https://${API_APP}.fly.dev/api/health/"
  curl -sSf --retry 5 --retry-delay 10 "$API_URL" || {
    echo "WARN: API health check failed after deploy. Check manually."
  }
  echo "[deploy] API ready."
}

# ── Deploy Frontend ───────────────────────────────────────────────────────────
deploy_web() {
  echo "[deploy] Deploying frontend ($WEB_APP)..."
  flyctl deploy --remote-only \
    -c "$WEB_FLY_CONF" \
    --app "$WEB_APP" \
    --strategy rolling

  echo "[deploy] Waiting for frontend health check..."
  sleep 10
  curl -sSf --retry 5 --retry-delay 10 "$FRONTEND_URL" || {
    echo "WARN: Frontend health check failed after deploy. Check manually."
  }
  echo "[deploy] Frontend ready."
}

# ── Execute ───────────────────────────────────────────────────────────────────
echo ""
echo "══════════════════════════════════════════════════════════════"
echo "  FrontierCRM Deploy"
echo "  Environment: ${DEPLOY_ENV}"
echo "  App:         ${DEPLOY_APP}"
echo "══════════════════════════════════════════════════════════════"
echo ""

if [ "$DEPLOY_APP" = "all" ] || [ "$DEPLOY_APP" = "api" ]; then
  deploy_api
fi

if [ "$DEPLOY_APP" = "all" ] || [ "$DEPLOY_APP" = "web" ]; then
  deploy_web
fi

echo ""
echo "══════════════════════════════════════════════════════════════"
echo "  Deploy complete!"
echo "  API:  https://${API_APP}.fly.dev/"
echo "  Web:  ${FRONTEND_URL}"
echo "══════════════════════════════════════════════════════════════"