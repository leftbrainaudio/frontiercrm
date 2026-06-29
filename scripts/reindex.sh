#!/usr/bin/env bash
# ── FrontierCRM Meilisearch Index Management ───────────────────────────────────
# Rebuild search indices for contacts, deals, and tasks.
# Designed to be run as a Celery Beat task or manually.
#
# Usage:
#   ./scripts/reindex.sh                                      # Full reindex
#   ./scripts/reindex.sh --staging                             # Staging
#   ./scripts/reindex.sh --check                               # Check index health
#   ./scripts/reindex.sh --drop-and-rebuild                    # Full reset
#
# Blast radius:
#   - Search is unavailable for ~30s during full rebuild.
#   - Delta sync is online only and does not block queries.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

DEPLOY_ENV="production"
ACTION="reindex"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --staging)          DEPLOY_ENV="staging" ;;
    --check)            ACTION="check" ;;
    --drop-and-rebuild) ACTION="rebuild" ;;
    *) echo "Unknown: $1"; exit 1 ;;
  esac
  shift
done

API_APP="$([ "$DEPLOY_ENV" = "staging" ] && echo "frontiercrm-api-staging" || echo "frontiercrm-api")"

command -v flyctl >/dev/null 2>&1 || { echo "FATAL: flyctl not found."; exit 1; }

case "$ACTION" in
  check)
    echo "[reindex] Checking Meilisearch index health for $API_APP..."
    flyctl ssh console -a "$API_APP" -C "python manage.py shell -c '
from apps.search.documents import ContactDocument, DealDocument, TaskDocument
for doc_cls in [ContactDocument, DealDocument, TaskDocument]:
    try:
        count = doc_cls().get_search().count()
        print(f\"{doc_cls.__name__}: {count} documents\")
    except Exception as e:
        print(f\"{doc_cls.__name__}: ERROR - {e}\")
'"
    ;;
  reindex)
    echo "[reindex] Full reindex for $API_APP..."
    flyctl ssh console -a "$API_APP" -C "python manage.py shell -c '
from apps.search.documents import ContactDocument, DealDocument, TaskDocument
for doc_cls in [ContactDocument, DealDocument, TaskDocument]:
    try:
        doc_cls().update_settings()
        doc_cls().reindex()
        print(f\"Reindexed {doc_cls.__name__}\")
    except Exception as e:
        print(f\"ERROR reindexing {doc_cls.__name__}: {e}\")
'"
    ;;
  rebuild)
    echo "[reindex] Dropping and rebuilding indices for $API_APP..."
    flyctl ssh console -a "$API_APP" -C "python manage.py shell -c '
from apps.search.documents import ContactDocument, DealDocument, TaskDocument
for doc_cls in [ContactDocument, DealDocument, TaskDocument]:
    try:
        client = doc_cls().get_client()
        client.delete_index(doc_cls.index_name())
        print(f\"Deleted index {doc_cls.index_name()}\")
    except Exception:
        pass
    doc_cls().update_settings()
    doc_cls().reindex()
    print(f\"Rebuilt {doc_cls.__name__}\")
'"
    ;;
esac

echo "[reindex] Done."