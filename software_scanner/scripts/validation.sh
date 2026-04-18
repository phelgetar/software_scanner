#!/usr/bin/env bash
#
###################################################################
# Project: software_scanner
# File: software_scanner/scripts/validation.sh
# Purpose: Install the git pre-commit hook that validates file headers.
#
# Description of code and how it works:
# Creates .githooks/pre-commit pointing at validate_headers.py and
# configures git to use .githooks/ as the hooks directory.
# Run once after cloning or whenever the hook needs to be reinstalled.
#
# Author: Tim Canady
# Created: 2025-09-28
#
# Version: 0.5.0
# Last Modified: 2026-04-17 by Tim Canady
#
# Revision History:
# - 0.5.0 (2026-04-17): Updated hook path for software_scanner layout.
# - 0.1.1 (2025-09-30): Fix hooks path configuration
###################################################################
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$REPO_ROOT"

mkdir -p .githooks

cat > .githooks/pre-commit <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
# Validate headers for all staged .py/.sh files
python software_scanner/scripts/validate_headers.py
EOF

chmod +x .githooks/pre-commit
git config core.hooksPath .githooks

echo "[✓] Pre-commit hook installed → .githooks/pre-commit"
echo "    Validates headers via: software_scanner/scripts/validate_headers.py"
