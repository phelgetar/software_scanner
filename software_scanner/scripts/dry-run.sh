#!/usr/bin/env bash
#
###################################################################
# Project: software_scanner
# File: software_scanner/scripts/dry-run.sh
# Purpose: Pre-commit smoke check — validate headers and versions.yml.
#
# Description of code and how it works:
# 1. Resolves the repo root from the script's own location so it can
#    be invoked from any working directory.
# 2. Verifies versions.yml exists alongside this script.
# 3. Runs validate_headers.py against the main package, tests, and
#    entry-point files, reporting any missing header fields.
#
# Author: Tim Canady
# Created: 2025-09-28
#
# Version: 0.5.0
# Last Modified: 2026-04-17 by Tim Canady
#
# Revision History:
# - 0.5.0 (2026-04-17): Rewritten for software_scanner project layout.
# - 0.1.1 (2025-09-30): Validate headers for .py — Tim Canady
# - 0.1.0 (2025-09-28): Initial — Tim Canady
###################################################################
#

set -euo pipefail

# Resolve locations regardless of where the script is invoked from
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$REPO_ROOT"

# ── 1. versions.yml check ─────────────────────────────────────
VERSIONS_FILE="$SCRIPT_DIR/versions.yml"
if [[ ! -f "$VERSIONS_FILE" ]]; then
  echo "❌ versions.yml missing."
  echo "   Run: python software_scanner/scripts/init_versions.py"
  exit 1
fi
echo "[✓] versions.yml found"

# ── 2. Header validation ──────────────────────────────────────
echo "[i] Validating headers in software_scanner/ tests/ main.py ..."
python "$SCRIPT_DIR/validate_headers.py" \
  software_scanner/ \
  tests/ \
  main.py

echo "[✓] Dry run passed."
