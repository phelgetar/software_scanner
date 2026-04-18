#!/usr/bin/env bash
#
###################################################################
# Project: software_scanner
# File: software_scanner/scripts/backup_snapshots.sh
# Purpose: Create a compressed DB snapshot in a secondary location.
#
# Author: Tim Canady
# Created: 2025-09-30
#
# Description:
#   Create a compressed DB snapshot in a secondary location, e.g. weekly.
#
# Version: 0.4.1
# Last Modified: 2025-10-04 by Tim Canady
#
# Revision History:
# - 0.1.0 (2025-09-30): Initial — Tim Canady
###################################################################
#

set -euo pipefail
if [ -f ".env" ]; then set -a; . ./.env; set +a; fi

# Reuse daily dump if exists
SRC_DIR="/var/backups/software_scanner/daily"
DST_DIR="/var/backups/software_scanner/snapshots"
mkdir -p "$DST_DIR"

LATEST="$(ls -1t "$SRC_DIR"/*.sql.gz | head -n1)"
: "${LATEST:?No daily backups in $SRC_DIR}"

STAMP="$(date "+%Y-%m-%d")"
OUT="$DST_DIR/snapshot_${STAMP}.sql.gz"

cp -p "$LATEST" "$OUT"
chmod 640 "$OUT"
echo "[✓] Snapshot copied to $OUT"

# Keep last 8 snapshots
ls -1t "$DST_DIR"/*.sql.gz 2>/dev/null | tail -n +9 | xargs -I {} rm -f "{}" || true
