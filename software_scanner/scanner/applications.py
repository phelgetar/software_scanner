#!/usr/bin/env python3
#
###################################################################
# Project: software_scanner
# File: software_scanner/scanner/applications.py
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
import os
import json

from software_scanner.utils import run_command


def get_applications():
    """Get all applications from /Applications and ~/Applications"""
    apps = []
    for apps_path in ["/Applications", os.path.expanduser("~/Applications")]:
        if not os.path.exists(apps_path):
            continue
        for item in os.listdir(apps_path):
            if item.endswith('.app'):
                app_path = os.path.join(apps_path, item)
                app_name = item.replace('.app', '')
                plist_path = os.path.join(app_path, 'Contents', 'Info.plist')
                apps.append({
                    'name': app_name,
                    'version': _get_app_version(plist_path),
                    'path': app_path,
                    'type': 'Application',
                })
    return apps


def get_system_profile_apps():
    """Get applications using system_profiler"""
    apps = []
    output = run_command("system_profiler SPApplicationsDataType -json")
    if output and not output.startswith("Error"):
        try:
            data = json.loads(output)
            for app in data.get('SPApplicationsDataType', []):
                apps.append({
                    'name': app.get('_name', 'Unknown'),
                    'version': app.get('version', 'Unknown'),
                    'path': app.get('path', 'Unknown'),
                    'type': 'System Profile',
                })
        except json.JSONDecodeError:
            pass
    return apps


def _get_app_version(plist_path):
    """Extract version from Info.plist"""
    if not os.path.exists(plist_path):
        return "Unknown"
    try:
        bundle_dir = plist_path.replace('/Info.plist', '')
        version = run_command(
            f"defaults read '{bundle_dir}' CFBundleShortVersionString 2>/dev/null"
        )
        if not version or version.startswith("Error"):
            version = run_command(
                f"defaults read '{bundle_dir}' CFBundleVersion 2>/dev/null"
            )
        return version if version and not version.startswith("Error") else "Unknown"
    except Exception:
        return "Unknown"
