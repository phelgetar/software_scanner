#!/usr/bin/env bash
#
###################################################################
# Project: software_scanner
# File: software_scanner/scripts/restore_files.sh
# Purpose: Restore project files or directories from compressed backups.
#
# Author: Tim Canady
# Created: 2025-09-30
#
# Description:
#   Restore project files or directories from compressed backups.
#   Supports restoring entire archive or a specific directory/file.
#
# Version: 0.4.1
# Last Modified: 2025-10-04 by Tim Canady
#
# Revision History:
# - 0.1.0 (2025-09-30): Initial — Tim Canady
###################################################################
#

set -euo pipefail

BACKUP_FILE="${1:-}"
TARGET_PATH="${2:-}"

if [[ -z "$BACKUP_FILE" ]]; then
  echo "Usage: $0 <backup.tar.gz> [target_subpath]"
  echo "Examples:"
  echo "  $0 /var/backups/software_scanner/snapshots/files_2025-09-30.tar.gz"
  echo "  $0 /var/backups/software_scanner/snapshots/files_2025-09-30.tar.gz software_scanner/cli.py"
  echo "  $0 /var/backups/software_scanner/snapshots/files_2025-09-30.tar.gz software_scanner/"
  exit 1
fi

if [[ ! -f "$BACKUP_FILE" ]]; then
  echo "Backup file not found: $BACKUP_FILE"
  exit 2
fi

echo "[i] Restoring from $BACKUP_FILE"

if [[ -n "$TARGET_PATH" ]]; then
  echo "[i] Restoring only $TARGET_PATH"
  tar -xvzf "$BACKUP_FILE" "$TARGET_PATH"
else
  echo "[i] Restoring entire archive"
  tar -xvzf "$BACKUP_FILE"
fi

echo "[✓] Restore complete."
