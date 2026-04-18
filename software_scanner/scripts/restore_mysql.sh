#!/usr/bin/env bash
#
###################################################################
# Project: software_scanner
# File: software_scanner/scripts/restore_mysql.sh
# Purpose: Restore the latest gzip'd backup into the configured DB.
#
# Author: Tim Canady
# Created: 2025-09-28
#
# Description:
#   Restore the latest gzip'd backup into the configured DB.
#
# Version: 0.4.1
# Last Modified: 2025-10-04 by Tim Canady
#
# Revision History:
# - 0.1.2 (2025-09-29): Safer selection; clear prompts — Tim Canady
# - 0.1.1 (2025-09-28): Add .env parsing — Tim Canady
# - 0.1.0 (2025-09-28): Initial — Tim Canady
###################################################################
#

set -euo pipefail
if [ -f ".env" ]; then set -a; . ./.env; set +a; fi

# Pull from DATABASE_URL if present
if [[ -n "${DATABASE_URL:-}" ]]; then
  proto_removed="${DATABASE_URL#*://}"
  creds="${proto_removed%@*}"
  hostdb="${proto_removed#*@}"
  user="${creds%%:*}"; pass="${creds#*:}"
  host="${hostdb%%:*}"; rest="${hostdb#*:}"
  port="${rest%%/*}"; db="${rest#*/}"
  MYSQL_HOST="${MYSQL_HOST:-$host}"
  MYSQL_PORT="${MYSQL_PORT:-$port}"
  MYSQL_USER="${MYSQL_USER:-$user}"
  MYSQL_PASSWORD="${MYSQL_PASSWORD:-$pass}"
  MYSQL_DB="${MYSQL_DB:-$db}"
fi

: "${MYSQL_HOST:=localhost}"
: "${MYSQL_PORT:=3306}"
: "${MYSQL_USER:?MYSQL_USER required}"
: "${MYSQL_PASSWORD:?MYSQL_PASSWORD required}"
: "${MYSQL_DB:?MYSQL_DB required}"

BACKUP_ROOT="/var/backups/software_scanner/daily"
LATEST="$(ls -1t "$BACKUP_ROOT"/*.sql.gz | head -n1)"
: "${LATEST:?No backups found in $BACKUP_ROOT}"

echo "Restoring $LATEST into $MYSQL_DB on $MYSQL_HOST:$MYSQL_PORT … (Ctrl+C to abort)"
sleep 2
gunzip -c "$LATEST" | mysql \
  --host="$MYSQL_HOST" --port="$MYSQL_PORT" \
  --user="$MYSQL_USER" --password="$MYSQL_PASSWORD" \
  "$MYSQL_DB"
echo "[✓] Restore complete."
