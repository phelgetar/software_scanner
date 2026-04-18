#!/usr/bin/env python3
#
###################################################################
# Project: software_scanner
# File: software_scanner/scripts/validate_headers.py
# Purpose: Validate presence of standardized headers in .py and .sh files.
#
# Description of code and how it works:
# Dual-mode validator:
#   - No args  → pre-commit hook mode: checks only git-staged .py/.sh files.
#   - With args → manual mode: walks the supplied files/directories and
#     validates every .py/.sh file found.
# Exits with code 1 and prints a report if any required header fields are
# missing; exits 0 on success.
#
# Author: Tim Canady
# Created: 2025-09-28
#
# Version: 0.5.0
# Last Modified: 2026-04-17 by Tim Canady
#
# Revision History:
# - 0.5.0 (2026-04-17): Dual-mode (staged + path-based); project renamed to software_scanner.
# - 0.4.1 (2025-10-04): Auto-synced update — Tim Canady
# - 0.1.0 (2025-09-22): Initial pre-commit hook — Tim Canady
###################################################################
#

import os
import subprocess
import sys
from pathlib import Path

REQUIRED_LINES = [
    "# Project:",
    "# File:",
    "# Version:",
    "# Last Modified:",
    "# Revision History:",
]

ALLOWED_EXTS = {".py", ".sh"}

EXCLUDE_DIRS = {
    ".git", ".idea", "__pycache__", "venv", ".venv",
    "node_modules", "dist", "build", ".mypy_cache", ".pytest_cache",
}


def get_staged_files():
    """Return staged .py/.sh files from git index."""
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        capture_output=True,
        text=True,
    )
    return [f for f in result.stdout.strip().splitlines() if f.endswith((".py", ".sh"))]


def iter_path_files(paths):
    """Yield every .py/.sh file reachable from the given paths."""
    seen = set()
    for path_str in paths:
        p = Path(path_str)
        if p.is_file():
            if p.suffix in ALLOWED_EXTS and p not in seen:
                seen.add(p)
                yield p
        elif p.is_dir():
            for fp in sorted(p.rglob("*")):
                if not fp.is_file():
                    continue
                if set(fp.parts) & EXCLUDE_DIRS:
                    continue
                if fp.suffix in ALLOWED_EXTS and fp not in seen:
                    seen.add(fp)
                    yield fp
        else:
            print(f"  ⚠  Path not found: {p}", file=sys.stderr)


def validate_file(path):
    """Return list of missing required header lines for one file."""
    try:
        content = Path(path).read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ["(unreadable)"]
    return [line for line in REQUIRED_LINES if line not in content]


def main():
    if sys.argv[1:]:
        files = list(iter_path_files(sys.argv[1:]))
        mode = "manual"
    else:
        files = get_staged_files()
        mode = "pre-commit"

    if not files:
        print("✅ No .py/.sh files to validate.")
        sys.exit(0)

    errors = {str(f): validate_file(f) for f in files}
    errors = {f: missing for f, missing in errors.items() if missing}

    if errors:
        print("❌ Header validation failed.\n")
        for f, missing in errors.items():
            print(f"  File: {f}")
            for m in missing:
                print(f"    - Missing: {m}")
        print()
        print("Tip: run  python software_scanner/scripts/add_headers.py --paths <dir>")
        sys.exit(1)

    count = len(files)
    if mode == "pre-commit":
        print(f"✅ All {count} staged file(s) contain valid headers.")
    else:
        print(f"✅ All {count} file(s) contain valid headers.")


if __name__ == "__main__":
    main()
