#!/usr/bin/env bash
#
###################################################################
# Project: software_scanner
# File: software_scanner/scripts/reinstall_alembic.sh
# Purpose: Reinstall project Python dependencies into the active virtual environment.
#
# Description of code and how it works:
# - Verifies a virtual environment is active.
# - Upgrades pip, then installs the project in editable mode.
# - Verifies the software-scanner CLI is available after install.
#
# Author: Tim Canady
# Created: 2025-09-28
#
# Version: 1.0.0
# Last Modified: 2026-04-17 by Tim Canady
#
# Revision History:
# - 1.0.0 (2026-04-17): Replaced Alembic-specific logic with software_scanner install.
# - 0.7.0 (2025-10-07): Original Alembic reinstall script (removed).
###################################################################
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Check a venv is active
if [[ -z "${VIRTUAL_ENV:-}" ]]; then
  echo "❌ No virtual environment is active."
  echo "   Activate one first:  source .venv/bin/activate"
  exit 1
fi

echo "[i] Python:  $(command -v python3)"
echo "[i] pip:     $(command -v pip)"
echo "[i] Venv:    $VIRTUAL_ENV"
echo ""

# Upgrade pip
echo "[i] Upgrading pip..."
python3 -m pip install --upgrade pip

# Install project in editable mode
echo "[i] Installing software-scanner (editable)..."
pip install -e "$REPO_ROOT"

# Verify CLI is available
if command -v software-scanner >/dev/null 2>&1; then
  echo "[✓] software-scanner CLI installed: $(command -v software-scanner)"
else
  echo "⚠  software-scanner not found on PATH — you may need to reactivate the venv."
fi

echo "[✓] Reinstall complete."
