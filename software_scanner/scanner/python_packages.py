#!/usr/bin/env python3
#
###################################################################
# Project: software_scanner
# File: software_scanner/scanner/python_packages.py
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


def get_python_packages():
    """Get installed Python packages via pip"""
    for pip_cmd in ['pip3', 'pip']:
        output = run_command(f"{pip_cmd} list --format=json 2>/dev/null")
        if output and not output.startswith("Error"):
            try:
                return [
                    {
                        'name': pkg.get('name', 'Unknown'),
                        'version': pkg.get('version', 'Unknown'),
                        'path': f'Python ({pip_cmd})',
                        'type': 'Python Package',
                    }
                    for pkg in json.loads(output)
                ]
            except json.JSONDecodeError:
                continue
    return []
