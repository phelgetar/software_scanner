#!/usr/bin/env python3
#
###################################################################
# Project: software_scanner
# File: software_scanner/scanner/npm_packages.py
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
import json

from software_scanner.utils import run_command


def get_npm_packages():
    """Get globally installed npm packages"""
    output = run_command("npm list -g --depth=0 --json 2>/dev/null")
    if not output or output.startswith("Error"):
        return []
    try:
        data = json.loads(output)
        return [
            {
                'name': name,
                'version': info.get('version', 'Unknown'),
                'path': 'npm (global)',
                'type': 'npm Package',
            }
            for name, info in data.get('dependencies', {}).items()
        ]
    except json.JSONDecodeError:
        return []
