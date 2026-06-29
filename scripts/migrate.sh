#!/usr/bin/env bash
# ── FrontierCRM Database Migration Runner ──────────────────────────────────────
# Runs Django migrations with Fly.io integration.
# Idempotent: re-running with no new migrations is a no-op (Django skips
# already-applied migrations).
#
# Usage:
#   ./scripts/migrate.sh                  # Migrate production
#   ./scripts/migrate.sh --staging         # Migrate staging
#   ./scripts/migrate.sh --check           # Dry-run (show pending migrations)
#   ./scripts/migrate.sh --app <app>       # Migrate a specific app only
#
# Blast radius:
#   - Backwards-incompatible migrations (column drops, table renames) may
#     cause brief errors for in-flight requests during the window between
#     migration and old-worker drain. Always deploy API first, then migrate.
#   - Long-running migrations (>30s) may timeout the SSH session.
#     For large tables, run manually with --timeout.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

DEPLOY_ENV="production"
CHECK_ONLY=false
APP_ARG=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --staging)  DEPLOY_ENV="staging" ;;
    --check)    CHECK_ONLY=true ;;
    --app)      APP_ARG="$2"; shift ;;
    *) echo "Unknown: $1"; exit 1 ;;
  esac
  shift
done

API_APP="$([ "$DEPLOY_ENV" = "staging" ] && echo "frontiercrm-api-staging" || echo "frontiercrm-api")"

command -v flyctl >/dev/null 2>&1 || { echo "FATAL: flyctl not found."; exit 1; }

MIGRATE_CMD="python manage.py migrate --noinput"
if [ -n "$APP_ARG" ]; then
  MIGRATE_CMD="$MIGRATE_CMD $APP_ARG"
fi
if [ "$CHECK_ONLY" = true ]; then
  MIGRATE_CMD="python manage.py showmigrations"
fi

echo "[migrate] Environment: $DEPLOY_ENV"
echo "[migrate] App: $API_APP"
echo "[migrate] Command: $MIGRATE_CMD"
echo ""

if [ "$CHECK_ONLY" = false ]; then
  echo "⚠  Running migrations on $DEPLOY_ENV database."
  echo "   Ensure the API is already deployed with the matching code."
  echo "   Old workers running the previous code will 500 on changed endpoints."
  echo ""
  read -rp "Continue? (type 'migrate' to confirm): " CONFIRM
  if [ "$CONFIRM" != "migrate" ]; then
    echo "Cancelled."
    exit 1
  fi
fi

flyctl ssh console -a "$API_APP" -C "$MIGRATE_CMD"

echo "[migrate] Done."