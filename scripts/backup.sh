#!/usr/bin/env bash
# ── FrontierCRM Backup Script ─────────────────────────────────────────────────
# Idempotent: re-running creates a new backup; does not overwrite old ones.
#
# Runs: pg_dump -> gzip -> upload to R2 (S3-compatible) -> cleanup old backups
#
# Usage:
#   ./scripts/backup.sh                    # Full backup with defaults
#   ./scripts/backup.sh --db-only          # Skip media
#   ./scripts/backup.sh --schema-only      # Schema-only (fast, for CI)
#
# Required env vars:
#   DATABASE_URL              - PostgreSQL connection string
#   AWS_ACCESS_KEY_ID         - R2 access key
#   AWS_SECRET_ACCESS_KEY     - R2 secret key
#   AWS_STORAGE_BUCKET_NAME   - R2 bucket name (default: frontiercrm-backups)
#   AWS_S3_ENDPOINT_URL       - R2 endpoint URL (e.g. https://<account>.r2.cloudflarestorage.com)
#
# Optional:
#   BACKUP_RETENTION_DAYS     - Days to keep backups (default: 30)
#   BACKUP_PREFIX             - S3 prefix (default: "backups/database")
#   AWS_S3_REGION_NAME        - Region (default: auto)

set -euo pipefail

# ── Config ────────────────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP_PREFIX="${BACKUP_PREFIX:-backups/database}"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-30}"
S3_REGION="${AWS_S3_REGION_NAME:-auto}"
CUTOFF_DATE="$(date -u -d "$RETENTION_DAYS days ago" +%Y%m%dT%H%M%SZ)"

# Parse args
SCHEMA_ONLY=false
DB_ONLY=false
for arg in "$@"; do
  case "$arg" in
    --schema-only) SCHEMA_ONLY=true ;;
    --db-only)     DB_ONLY=true ;;
  esac
done

# ── Prerequisites ──────────────────────────────────────────────────────────────
command -v pg_dump >/dev/null 2>&1 || { echo "FATAL: pg_dump not found. Install postgresql-client."; exit 1; }
command -v aws >/dev/null 2>&1 || { echo "FATAL: aws CLI not found. Install with: pip install awscli"; exit 1; }

# Validate required env vars
for var in DATABASE_URL AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_STORAGE_BUCKET_NAME AWS_S3_ENDPOINT_URL; do
  if [ -z "${!var:-}" ]; then
    echo "FATAL: $var is not set"
    exit 1
  fi
done

# ── Backup Database ───────────────────────────────────────────────────────────
echo "[${TIMESTAMP}] Starting database backup..."

BACKUP_FILE="${PROJECT_DIR}/tmp/backups/frontiercrm_${TIMESTAMP}.sql.gz"
mkdir -p "$(dirname "$BACKUP_FILE")"

if [ "$SCHEMA_ONLY" = true ]; then
  echo "[${TIMESTAMP}] Schema-only dump..."
  pg_dump "$DATABASE_URL" --schema-only --no-owner --no-acl | gzip > "$BACKUP_FILE"
else
  echo "[${TIMESTAMP}] Full database dump (custom format)..."
  pg_dump "$DATABASE_URL" --no-owner --no-acl --format=custom | gzip > "$BACKUP_FILE"
fi

BACKUP_SIZE=$(stat -f%z "$BACKUP_FILE" 2>/dev/null || stat -c%s "$BACKUP_FILE" 2>/dev/null)
echo "[${TIMESTAMP}] Backup size: $BACKUP_SIZE bytes"

# ── Upload to R2 ──────────────────────────────────────────────────────────────
S3_KEY="${BACKUP_PREFIX}/frontiercrm_${TIMESTAMP}.sql.gz"
echo "[${TIMESTAMP}] Uploading to s3://${AWS_STORAGE_BUCKET_NAME}/${S3_KEY}..."

aws s3 cp "$BACKUP_FILE" "s3://${AWS_STORAGE_BUCKET_NAME}/${S3_KEY}" \
  --endpoint-url "$AWS_S3_ENDPOINT_URL" \
  --region "$S3_REGION" \
  --only-show-errors

echo "[${TIMESTAMP}] Upload complete."

# ── Cleanup Old Backups ──────────────────────────────────────────────────────
echo "[${TIMESTAMP}] Cleaning backups older than ${RETENTION_DAYS} days..."

aws s3api list-objects-v2 \
  --bucket "$AWS_STORAGE_BUCKET_NAME" \
  --prefix "$BACKUP_PREFIX/" \
  --endpoint-url "$AWS_S3_ENDPOINT_URL" \
  --query "Contents[?LastModified<='${CUTOFF_DATE}'].Key" \
  --output text 2>/dev/null | while read -r key; do
    if [ -n "$key" ]; then
      echo "[${TIMESTAMP}] Deleting expired backup: $key"
      aws s3 rm "s3://${AWS_STORAGE_BUCKET_NAME}/${key}" \
        --endpoint-url "$AWS_S3_ENDPOINT_URL" \
        --only-show-errors
    fi
done

echo "[${TIMESTAMP}] Cleaning local temp files..."
rm -f "$BACKUP_FILE"

echo "[${TIMESTAMP}] Backup complete: ${S3_KEY} (${BACKUP_SIZE} bytes)"
echo "[${TIMESTAMP}] Retention: ${RETENTION_DAYS} days"

# ── Upload Media (if not --db-only) ──────────────────────────────────────────
if [ "$DB_ONLY" != true ] && [ "$SCHEMA_ONLY" != true ]; then
  MEDIA_DIR="${PROJECT_DIR}/media"
  if [ -d "$MEDIA_DIR" ] && [ "$(ls -A "$MEDIA_DIR" 2>/dev/null)" ]; then
    MEDIA_TIMESTAMP="${TIMESTAMP}"
    MEDIA_PREFIX="${BACKUP_PREFIX/\/database/\/media}/${MEDIA_TIMESTAMP}"
    echo "[${TIMESTAMP}] Syncing media to s3://${AWS_STORAGE_BUCKET_NAME}/${MEDIA_PREFIX}/..."

    aws s3 sync "$MEDIA_DIR" "s3://${AWS_STORAGE_BUCKET_NAME}/${MEDIA_PREFIX}/" \
      --endpoint-url "$AWS_S3_ENDPOINT_URL" \
      --region "$S3_REGION" \
      --only-show-errors

    echo "[${TIMESTAMP}] Media sync complete."
  else
    echo "[${TIMESTAMP}] Media directory empty or missing, skipping."
  fi
fi

echo "[${TIMESTAMP}] All backup tasks complete."