#!/usr/bin/env python3
#
###################################################################
# Project: software_scanner
# File: software_scanner/scanner/homebrew.py
# Purpose: Utility script
#
# Description of code and how it works:
# Helper functionality
#
# Author: Tim Canady
# Created: 2026-04-17
#
# Version: 1.0.0
# Last Modified: 2026-04-17 by Tim Canady
#
# Revision History:
# - 1.0.0 (2026-04-17): Initial version
###################################################################
#
from software_scanner.utils import run_command


def get_homebrew_packages():
    """Get Homebrew installed formulae and casks"""
    packages = []
    if not _is_brew_available():
        return packages

    for brew_type, flag in [('Homebrew Formula', '--formula'), ('Homebrew Cask', '--cask')]:
        output = run_command(f"brew list {flag} --versions")
        if output and not output.startswith("Error"):
            for line in output.split('\n'):
                parts = line.strip().split(' ', 1)
                if len(parts) == 2:
                    packages.append({
                        'name': parts[0],
                        'version': parts[1],
                        'path': 'Homebrew',
                        'type': brew_type,
                    })
    return packages


def _is_brew_available():
    result = run_command("which brew")
    return bool(result) and not result.startswith("Error")
