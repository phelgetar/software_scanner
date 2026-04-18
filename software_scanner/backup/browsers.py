#!/usr/bin/env python3
#
###################################################################
# Project: software_scanner
# File: software_scanner/backup/browsers.py
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
import shutil


_BROWSER_CONFIGS = {
    'Firefox': os.path.expanduser("~/Library/Application Support/Firefox/Profiles"),
    'Safari': os.path.expanduser("~/Library/Safari"),
    'Brave': os.path.expanduser("~/Library/Application Support/BraveSoftware/Brave-Browser"),
    'Edge': os.path.expanduser("~/Library/Application Support/Microsoft Edge"),
    'Opera': os.path.expanduser("~/Library/Application Support/com.operasoftware.Opera"),
}

_SAFARI_FILES = [
    'Bookmarks.plist', 'History.db', 'Cookies.binarycookies',
    'Downloads.plist', 'LastSession.plist', 'TopSites.plist',
]


def backup_other_browser_profiles(backup_dir):
    """Backup profiles from Firefox, Safari, Brave, Edge, and Opera"""
    print("\nBacking up other browser profiles...")
    backed_up = []

    for browser_name, browser_path in _BROWSER_CONFIGS.items():
        if not os.path.exists(browser_path):
            continue

        print(f"\n  Processing {browser_name}...")
        browser_backup_dir = os.path.join(backup_dir, f"{browser_name}_Backup")

        try:
            if browser_name == 'Safari':
                _backup_safari(browser_path, browser_backup_dir)
            else:
                shutil.copytree(browser_path, browser_backup_dir, dirs_exist_ok=True)
                print(f"    ✓ Backed up {browser_name} profiles")
            backed_up.append(browser_name)
        except Exception as e:
            print(f"    ✗ Error backing up {browser_name}: {e}")

    return backed_up


def _backup_safari(safari_path, backup_dir):
    os.makedirs(backup_dir, exist_ok=True)
    for filename in _SAFARI_FILES:
        src = os.path.join(safari_path, filename)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(backup_dir, filename))
            print(f"    ✓ {filename}")
