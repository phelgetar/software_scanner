#!/usr/bin/env python3
#
###################################################################
# Project: software_scanner
# File: software_scanner/backup/chrome.py
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
import shutil
from datetime import datetime

from software_scanner.utils import format_size


_CHROME_PATHS = [
    os.path.expanduser("~/Library/Application Support/Google/Chrome"),
    os.path.expanduser("~/Library/Application Support/Google/Chrome Canary"),
    os.path.expanduser("~/Library/Application Support/Chromium"),
]

_FILES_TO_BACKUP = {
    'Bookmarks': 'Bookmarks',
    'Bookmarks.bak': 'Bookmarks_Backup',
    'Cookies': 'Cookies',
    'Preferences': 'Preferences.json',
    'History': 'History',
    'Login Data': 'Login_Data',
    'Web Data': 'Web_Data',
    'Favicons': 'Favicons',
    'Top Sites': 'Top_Sites',
    'Shortcuts': 'Shortcuts',
    'Network Action Predictor': 'Network_Action_Predictor',
    'Current Session': 'Current_Session',
    'Current Tabs': 'Current_Tabs',
    'Last Session': 'Last_Session',
    'Last Tabs': 'Last_Tabs',
}


def backup_chrome_profiles(backup_dir):
    """Backup Chrome profiles including bookmarks, cookies, and settings"""
    print("\nBacking up Chrome profiles...")

    backup_info = {'timestamp': datetime.now().isoformat(), 'profiles': []}

    for chrome_path in _CHROME_PATHS:
        if not os.path.exists(chrome_path):
            continue

        browser_name = os.path.basename(chrome_path)
        browser_backup_dir = os.path.join(backup_dir, browser_name.replace(' ', '_'))
        os.makedirs(browser_backup_dir, exist_ok=True)
        print(f"\n  Processing {browser_name}...")

        _backup_local_state(chrome_path, browser_backup_dir)

        profiles = [
            (item, os.path.join(chrome_path, item))
            for item in os.listdir(chrome_path)
            if os.path.isdir(os.path.join(chrome_path, item))
            and (item.startswith('Profile ') or item == 'Default')
        ]
        print(f"    Found {len(profiles)} profile(s)")

        for profile_name, profile_path in profiles:
            profile_info = _backup_single_profile(
                profile_name, profile_path, browser_name, browser_backup_dir
            )
            backup_info['profiles'].append(profile_info)

    manifest_path = os.path.join(backup_dir, 'backup_manifest.json')
    with open(manifest_path, 'w') as f:
        json.dump(backup_info, f, indent=2)
    print(f"\n  Backup manifest saved to: {manifest_path}")
    return backup_info


def _backup_local_state(chrome_path, browser_backup_dir):
    local_state_path = os.path.join(chrome_path, 'Local State')
    if os.path.exists(local_state_path):
        try:
            shutil.copy2(local_state_path, os.path.join(browser_backup_dir, 'Local_State.json'))
            print("    ✓ Backed up Local State")
        except Exception as e:
            print(f"    ✗ Error backing up Local State: {e}")


def _backup_single_profile(profile_name, profile_path, browser_name, browser_backup_dir):
    print(f"\n    Backing up profile: {profile_name}")
    profile_backup_dir = os.path.join(browser_backup_dir, profile_name.replace(' ', '_'))
    os.makedirs(profile_backup_dir, exist_ok=True)

    profile_info = {
        'name': profile_name,
        'browser': browser_name,
        'backed_up_items': [],
    }

    for source_name, dest_name in _FILES_TO_BACKUP.items():
        source_path = os.path.join(profile_path, source_name)
        if os.path.exists(source_path):
            try:
                shutil.copy2(source_path, os.path.join(profile_backup_dir, dest_name))
                file_size = os.path.getsize(source_path)
                profile_info['backed_up_items'].append(
                    {'file': source_name, 'size_bytes': file_size}
                )
                print(f"      ✓ {source_name} ({format_size(file_size)})")
            except Exception as e:
                print(f"      ✗ Error backing up {source_name}: {e}")

    for folder_name in ('Extensions', 'Storage', 'Sessions'):
        folder_path = os.path.join(profile_path, folder_name)
        if os.path.exists(folder_path):
            try:
                shutil.copytree(folder_path, os.path.join(profile_backup_dir, folder_name),
                                dirs_exist_ok=True)
                if folder_name == 'Extensions':
                    count = len([d for d in os.listdir(folder_path)
                                 if os.path.isdir(os.path.join(folder_path, d))])
                    profile_info['extension_count'] = count
                    print(f"      ✓ Extensions folder ({count} extension(s))")
                else:
                    label = "tab restore data" if folder_name == 'Sessions' else folder_name
                    print(f"      ✓ {folder_name} folder ({label})")
            except Exception as e:
                print(f"      ✗ Error backing up {folder_name}: {e}")

    tabs_path = os.path.join(profile_path, 'Current Tabs')
    if os.path.exists(tabs_path):
        tab_count = _extract_tab_count(tabs_path)
        if tab_count:
            profile_info['current_open_tabs'] = tab_count
            print(f"      ℹ Currently has {tab_count} open tab(s)")

    return profile_info


def _extract_tab_count(tabs_file_path):
    try:
        with open(tabs_file_path, 'rb') as f:
            content = f.read()
            count = content.count(b'http://') + content.count(b'https://')
            return count if count > 0 else None
    except Exception:
        return None
