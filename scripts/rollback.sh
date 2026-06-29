#!/usr/bin/env bash
# ── FrontierCRM Rollback Script ───────────────────────────────────────────────
# One-command rollback to a previous release.
# Idempotent: re-running rollback to the same version is safe (Fly.io handles
# idempotency — deploying the same image is a no-op).
#
# Usage:
#   ./scripts/rollback.sh                      # Rollback API to previous release
#   ./scripts/rollback.sh --app web             # Rollback frontend only
#   ./scripts/rollback.sh --version <version>   # Rollback to specific version
#   ./scripts/rollback.sh --list                # List recent releases
#   ./scripts/rollback.sh --staging              # Rollback staging
#
# Blast radius:
#   - API rollback: brief 503 during process swap (~5s). Existing WebSocket
#     connections are dropped. Running Celery tasks may be duplicated or lost.
#   - Web rollback: brief 503 during nginx restart (~2s). In-flight API calls
#     from the browser may fail; refresh resolves.
#   - Database rollback: NOT handled here. If you need to undo a migration,
#     run the reverse migration manually first, then rollback the code.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

# ── Parse Args ────────────────────────────────────────────────────────────────
DEPLOY_ENV="production"
ROLLBACK_APP="api"
ROLLBACK_VERSION=""
LIST_ONLY=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --staging)        DEPLOY_ENV="staging" ;;
    --app)            ROLLBACK_APP="$2"; shift ;;
    --version)        ROLLBACK_VERSION="$2"; shift ;;
    --list)           LIST_ONLY=true ;;
    --help|-h)
      echo "Usage: $0 [--staging] [--app api|web] [--version <version>] [--list]"
      echo ""
      echo "  --staging         Rollback staging environment"
      echo "  --app api|web     Rollback specified app (default: api)"
      echo "  --version <ver>   Rollback to specific release version"
      echo "  --list            List recent releases (no rollback)"
      exit 0 ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
  shift
done

if [ "$DEPLOY_ENV" = "staging" ]; then
  API_APP="frontiercrm-api-staging"
  WEB_APP="frontiercrm-web-staging"
else
  API_APP="frontiercrm-api"
  WEB_APP="frontiercrm-web"
fi

FLY_CONF="fly.toml"
WEB_FLY_CONF="frontend/fly.web.toml"

# ── Prerequisites ──────────────────────────────────────────────────────────────
command -v flyctl >/dev/null 2>&1 || { echo "FATAL: flyctl not found."; exit 1; }

# ── List Mode ─────────────────────────────────────────────────────────────────
if [ "$LIST_ONLY" = true ]; then
  echo "Recent releases for $API_APP:"
  flyctl releases list -a "$API_APP" 2>/dev/null | head -15 || echo "  (no releases found)"
  echo ""
  echo "Recent releases for $WEB_APP:"
  flyctl releases list -a "$WEB_APP" 2>/dev/null | head -15 || echo "  (no releases found)"
  exit 0
fi

# ── Confirm ───────────────────────────────────────────────────────────────────
APP_LABEL="$([ "$ROLLBACK_APP" = "api" ] && echo "$API_APP" || echo "$WEB_APP")"
echo ""
echo "⚠  ROLLBACK WARNING"
echo "   App:        $APP_LABEL"
echo "   Environment: $DEPLOY_ENV"
echo "   Target:     ${ROLLBACK_VERSION:-previous release}"
echo ""
echo "Blast radius:"
echo "  - Brief 503 during process swap (~5s)"
echo "  - WebSocket connections dropped"
echo "  - In-flight Celery tasks may be duplicated"
echo ""

read -rp "Continue? (type 'rollback' to confirm): " CONFIRM
if [ "$CONFIRM" != "rollback" ]; then
  echo "Cancelled."
  exit 1
fi

# ── Rollback ──────────────────────────────────────────────────────────────────
if [ "$ROLLBACK_APP" = "api" ]; then
  FLY_APP="$API_APP"
  FLY_CONF_FILE="$FLY_CONF"
elif [ "$ROLLBACK_APP" = "web" ]; then
  FLY_APP="$WEB_APP"
  FLY_CONF_FILE="$WEB_FLY_CONF"
else
  echo "FATAL: Unknown app '$ROLLBACK_APP'. Use 'api' or 'web'."
  exit 1
fi

echo "[rollback] Starting rollback of $FLY_APP..."

if [ -n "$ROLLBACK_VERSION" ]; then
  echo "[rollback] Rolling back to version: $ROLLBACK_VERSION"
  flyctl deploy --remote-only \
    -c "$FLY_CONF_FILE" \
    --app "$FLY_APP" \
    --image "ref:${ROLLBACK_VERSION}" \
    --strategy immediate
else
  echo "[rollback] Rolling back to previous release..."
  flyctl releases list -a "$FLY_APP" --format json 2>/dev/null | \
    python3 -c "
import json, sys
releases = json.load(sys.stdin)
if len(releases) < 2:
    print('No previous release to rollback to.', file=sys.stderr)
    sys.exit(1)
prev = releases[1]  # index 0 is current
print(prev['id'], end='')
" > /tmp/rollback_version.txt 2>/dev/null || {
    echo "FATAL: Could not determine previous release. Try --version instead."
    exit 1
  }
  PREV_VERSION=$(cat /tmp/rollback_version.txt)
  echo "[rollback] Previous release ID: $PREV_VERSION"
  flyctl deploy --remote-only \
    -c "$FLY_CONF_FILE" \
    --app "$FLY_APP" \
    --image "ref:${PREV_VERSION}" \
    --strategy immediate
fi

# ── Post-rollback Health Check ────────────────────────────────────────────────
echo "[rollback] Waiting for app to stabilise..."
sleep 15

if [ "$ROLLBACK_APP" = "api" ]; then
  echo "[rollback] Verifying API health..."
  API_URL="https://${FLY_APP}.fly.dev/api/health/"
  curl -sSf --retry 5 --retry-delay 10 "$API_URL" && \
    echo "[rollback] API health check passed" || \
    echo "[rollback] WARNING: API health check failed — investigate manually."
else
  echo "[rollback] Verifying frontend health..."
  curl -sSf --retry 5 --retry-delay 10 "https://${FLY_APP}.fly.dev/" && \
    echo "[rollback] Frontend health check passed" || \
    echo "[rollback] WARNING: Frontend health check failed — investigate manually."
fi

echo "[rollback] Rollback of $FLY_APP complete."