#!/usr/bin/env python3
#
###################################################################
# Project: software_scanner
# File: software_scanner/cli.py
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
import os
from datetime import datetime

from software_scanner.scanner import (
    get_applications,
    get_system_profile_apps,
    get_homebrew_packages,
    get_python_packages,
    get_npm_packages,
)
from software_scanner.backup import (
    backup_chrome_profiles,
    backup_other_browser_profiles,
    backup_application_settings,
)
from software_scanner.restore import restore_from_backup
from software_scanner.reports import generate_report


def main():
    print("=" * 60)
    print("macOS Software Scanner & Profile Backup/Restore Tool")
    print("=" * 60)
    print()
    print("What would you like to do?")
    print("  1. Backup  - Create a backup of software list and profiles")
    print("  2. Restore - Restore from a previous backup")
    print("  3. Both    - Create backup AND restore from existing backup")

    while True:
        choice = input("\nEnter your choice (1, 2, or 3): ").strip()
        if choice in ('1', '2', '3'):
            break
        print("Invalid choice. Please enter 1, 2, or 3.")

    if choice in ('2', '3'):
        restore_from_backup()
        if choice == '2':
            return
        print("\n" + "=" * 60)
        print("Now proceeding with backup...")
        print("=" * 60)

    _run_backup()


def _run_backup():
    print("\nScanning your Mac for installed software...")

    scanners = [
        ("Applications folders", get_applications),
        ("system_profiler", get_system_profile_apps),
        ("Homebrew packages", get_homebrew_packages),
        ("Python packages", get_python_packages),
        ("npm packages", get_npm_packages),
    ]

    all_software = []
    for label, fn in scanners:
        print(f"Scanning {label}...")
        items = fn()
        all_software.extend(items)
        print(f"  Found {len(items)} item(s)")

    print(f"\nTotal software items found: {len(all_software)}")

    print("\nGenerating software reports...")
    for fmt in ('txt', 'csv', 'json'):
        filename = generate_report(all_software, fmt)
        print(f"  {fmt.upper():4s}: {filename}")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = f"mac_backup_{timestamp}"
    os.makedirs(backup_dir, exist_ok=True)
    print(f"\n{'=' * 60}")
    print(f"Creating backups in: {backup_dir}")
    print("=" * 60)

    chrome_info = backup_chrome_profiles(backup_dir)
    other_browsers = backup_other_browser_profiles(backup_dir)
    settings_info = backup_application_settings(backup_dir)

    summary = {
        'timestamp': datetime.now().isoformat(),
        'backup_directory': backup_dir,
        'chrome_profiles_backed_up': len(chrome_info.get('profiles', [])),
        'other_browsers_backed_up': other_browsers,
        'preference_files_backed_up': settings_info['preference_files'],
        'apps_with_session_data': settings_info['apps_with_sessions'],
    }
    summary_file = os.path.join(backup_dir, 'backup_summary.json')
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)

    print("\n" + "=" * 60)
    print("BACKUP SUMMARY")
    print("=" * 60)
    print(f"Chrome profiles backed up:  {summary['chrome_profiles_backed_up']}")
    print(f"Other browsers backed up:   {', '.join(other_browsers) or 'None found'}")
    print(f"Preference files backed up: {settings_info['preference_files']}")
    if settings_info['apps_with_sessions']:
        print("\nApplications with session data backed up:")
        for app in settings_info['apps_with_sessions']:
            print(f"  • {app['app']} - {app['description']}")
    print(f"\nBackup saved to: {backup_dir}/")
    print("✓ Backup complete!")
