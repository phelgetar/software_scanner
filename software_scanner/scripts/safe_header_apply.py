#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
###################################################################
# Project: software_scanner
# File: software_scanner/scripts/safe_header_apply.py
# Purpose: Convenience wrapper for apply_headers.py with dry-run confirmation.
#
# Author: Tim Canady
# Created: 2025-09-30
#
# Version: 0.4.1
# Last Modified: 2025-10-04 by Tim Canady
#
# Revision History:
# - 0.1.0 (2025-09-30): Initial — Tim Canady
###################################################################
#

import argparse
import subprocess
import sys


def main():
    p = argparse.ArgumentParser()
    p.add_argument("paths", nargs="*", default=["software_scanner", "tests"])
    p.add_argument("--ext", nargs="+", default=[".py"])
    p.add_argument("--yes", action="store_true", help="Apply without prompt")
    p.add_argument("--date", default=None)
    p.add_argument("--version", default=None)
    p.add_argument("--author", default=None)
    args = p.parse_args()

    base = ["python", "scripts/apply_headers.py"] + args.paths + ["--ext"] + args.ext
    if args.date:    base += ["--date", args.date]
    if args.version: base += ["--version", args.version]
    if args.author:  base += ["--author", args.author]

    print("=== DRY RUN ===")
    subprocess.run(base + ["--dry-run"], check=True)
    if not args.yes:
        resp = input("Apply changes? [y/N] ").strip().lower()
        if resp != "y":
            print("Aborted.")
            sys.exit(0)
    print("=== APPLYING ===")
    subprocess.run(base, check=True)


if __name__ == "__main__":
    main()
