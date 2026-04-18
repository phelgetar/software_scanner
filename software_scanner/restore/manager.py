#!/usr/bin/env python3
#
###################################################################
# Project: software_scanner
# File: software_scanner/restore/manager.py
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

from .installer import analyze_backup_and_offer_installation, check_if_installed


def find_backup_directories():
    """Find all mac_backup_* directories in the current working directory"""
    backups = []
    for item in os.listdir('.'):
        if not (os.path.isdir(item) and item.startswith('mac_backup_')):
            continue
        summary_path = os.path.join(item, 'backup_summary.json')
        if os.path.exists(summary_path):
            try:
                with open(summary_path) as f:
                    summary = json.load(f)
                backups.append({
                    'directory': item,
                    'timestamp': summary.get('timestamp', 'Unknown'),
                    'summary': summary,
                })
            except Exception:
                pass
    return sorted(backups, key=lambda x: x['timestamp'], reverse=True)


def restore_from_backup():
    """Interactive restore orchestrator"""
    print("=" * 60)
    print("RESTORE FROM BACKUP")
    print("=" * 60)

    backups = find_backup_directories()
    if not backups:
        print("No backup directories found in the current location.")
        print("Run this script from the directory containing your mac_backup_* folders.")
        return

    print("\nAvailable backups:")
    for i, backup in enumerate(backups, 1):
        ts = _format_timestamp(backup['timestamp'])
        s = backup['summary']
        print(f"  {i}. {backup['directory']}")
        print(f"     Created: {ts}")
        print(f"     Chrome profiles: {s.get('chrome_profiles_backed_up', 0)}")
        print(f"     Apps with sessions: {len(s.get('apps_with_session_data', []))}")

    backup_dir = _select_backup(backups)
    if backup_dir is None:
        return

    installed_apps = analyze_backup_and_offer_installation(backup_dir)

    print("\n" + "=" * 60)
    print("RESTORE OPTIONS")
    print("=" * 60)
    print("\nWhat would you like to restore?")
    print("  1. Everything (all profiles and settings)")
    print("  2. Chrome profiles only")
    print("  3. Application settings and sessions only")
    print("  4. Custom selection")

    while True:
        restore_choice = input("\nEnter your choice (1-4): ").strip()
        if restore_choice in ['1', '2', '3', '4']:
            break
        print("Invalid choice. Please enter 1, 2, 3, or 4.")

    print("\n⚠ WARNING: Restoring will overwrite existing data!")
    print("   Make sure all applications are closed before continuing.")
    if input("\nContinue with restore? (yes/no): ").strip().lower() != 'yes':
        print("Restore cancelled.")
        return

    restored_items = []

    if restore_choice in ('1', '2'):
        restored_items.extend(_restore_chrome(backup_dir))

    if restore_choice in ('1', '3'):
        restored_items.extend(_restore_app_support(backup_dir))
        restored_items.extend(_restore_preferences(backup_dir))
        restored_items.extend(_restore_ssh(backup_dir))

    _print_restore_summary(installed_apps, restored_items)


def restore_chrome_profile(backup_dir, profile_name='Default'):
    """Restore a single Chrome profile from backup"""
    chrome_backup = os.path.join(backup_dir, 'Google_Chrome')
    if not os.path.exists(chrome_backup):
        print("  ✗ No Chrome backup found")
        return False

    chrome_path = os.path.expanduser("~/Library/Application Support/Google/Chrome")
    if not os.path.exists(chrome_path):
        print("  ⚠ Chrome is not installed. Skipping Chrome restore.")
        return False

    profile_backup_path = os.path.join(chrome_backup, profile_name.replace(' ', '_'))
    if not os.path.exists(profile_backup_path):
        print(f"  ✗ Profile '{profile_name}' not found in backup")
        return False

    profile_path = os.path.join(chrome_path, profile_name)
    if os.path.exists(profile_path):
        print(f"  ⚠ Profile '{profile_name}' already exists")
        if input(f"    Overwrite existing profile? (y/n): ").strip().lower() != 'y':
            return False
        backup_existing = f"{profile_path}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copytree(profile_path, backup_existing)
        shutil.rmtree(profile_path)

    try:
        shutil.copytree(profile_backup_path, profile_path)
        print(f"    ✓ Restored Chrome profile '{profile_name}'")
        return True
    except Exception as e:
        print(f"    ✗ Error restoring profile: {e}")
        return False


def restore_application_support(backup_dir, app_name):
    """Restore a single app's Application Support data"""
    app_backup_path = os.path.join(
        backup_dir, 'Application_Settings', 'Application_Support', app_name
    )
    if not os.path.exists(app_backup_path):
        return False

    app_support_path = os.path.expanduser(f"~/Library/Application Support/{app_name}")

    if not check_if_installed(app_name, 'Application') and not os.path.exists(app_support_path):
        print(f"  ⚠ {app_name} doesn't appear to be installed")
        if input(f"    Restore {app_name} data anyway? (y/n): ").strip().lower() != 'y':
            return False

    if os.path.exists(app_support_path):
        print(f"  ⚠ {app_name} data already exists")
        if input(f"    Overwrite existing {app_name} data? (y/n): ").strip().lower() != 'y':
            return False
        backup_existing = (
            f"{app_support_path}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        shutil.copytree(app_support_path, backup_existing)
        shutil.rmtree(app_support_path)

    try:
        shutil.copytree(app_backup_path, app_support_path)
        print(f"  ✓ Restored {app_name} data")
        return True
    except Exception as e:
        print(f"  ✗ Error restoring {app_name}: {e}")
        return False


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _select_backup(backups):
    while True:
        try:
            choice = input(f"\nSelect backup to restore (1-{len(backups)}) or 'q' to quit: ").strip()
            if choice.lower() == 'q':
                return None
            idx = int(choice) - 1
            if 0 <= idx < len(backups):
                return backups[idx]['directory']
            print(f"Please enter a number between 1 and {len(backups)}")
        except ValueError:
            print("Please enter a valid number")


def _format_timestamp(ts):
    if isinstance(ts, str) and 'T' in ts:
        try:
            return datetime.fromisoformat(ts.replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M:%S')
        except Exception:
            pass
    return ts


def _restore_chrome(backup_dir):
    restored = []
    print("\nRestoring Chrome profiles...")
    chrome_backup = os.path.join(backup_dir, 'Google_Chrome')
    if not os.path.exists(chrome_backup):
        return restored

    for item in os.listdir(chrome_backup):
        if item in {'Default', 'Profile_1', 'Profile_2', 'Profile_3', 'Profile_4', 'Profile_5'}:
            if restore_chrome_profile(backup_dir, item.replace('_', ' ')):
                restored.append(f"Chrome {item}")

    local_state_backup = os.path.join(chrome_backup, 'Local_State.json')
    chrome_path = os.path.expanduser("~/Library/Application Support/Google/Chrome")
    if os.path.exists(local_state_backup) and os.path.exists(chrome_path):
        try:
            shutil.copy2(local_state_backup, os.path.join(chrome_path, 'Local State'))
            print("  ✓ Restored Chrome Local State")
        except Exception as e:
            print(f"  ✗ Error restoring Local State: {e}")

    return restored


def _restore_app_support(backup_dir):
    restored = []
    print("\nRestoring Application Support data...")
    app_support_backup = os.path.join(backup_dir, 'Application_Settings', 'Application_Support')
    if not os.path.exists(app_support_backup):
        return restored

    apps = os.listdir(app_support_backup)
    print(f"  Found {len(apps)} applications with backed up data\n")
    for app_name in apps:
        print(f"  Restoring {app_name}...")
        if restore_application_support(backup_dir, app_name):
            restored.append(app_name)
    return restored


def _restore_preferences(backup_dir):
    restored = []
    print("\nRestoring Preferences...")
    prefs_backup = os.path.join(backup_dir, 'Application_Settings', 'Preferences')
    if not os.path.exists(prefs_backup):
        return restored

    prefs_dir = os.path.expanduser("~/Library/Preferences")
    count = 0
    for pref_file in os.listdir(prefs_backup):
        try:
            shutil.copy2(os.path.join(prefs_backup, pref_file),
                         os.path.join(prefs_dir, pref_file))
            count += 1
        except Exception:
            pass
    print(f"  ✓ Restored {count} preference files")
    if count:
        restored.append(f"{count} preference files")
    return restored


def _restore_ssh(backup_dir):
    restored = []
    print("\nRestoring SSH configuration...")
    ssh_backup = os.path.join(backup_dir, 'Application_Settings', 'SSH')
    if not os.path.exists(ssh_backup):
        return restored

    ssh_dir = os.path.expanduser("~/.ssh")
    if os.path.exists(ssh_dir):
        if input("  ⚠ SSH config already exists. Overwrite? (y/n): ").strip().lower() != 'y':
            print("    Skipping SSH restore...")
            return restored
        backup_existing = f"{ssh_dir}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copytree(ssh_dir, backup_existing)
        shutil.rmtree(ssh_dir)

    shutil.copytree(ssh_backup, ssh_dir)
    os.chmod(ssh_dir, 0o700)
    for root, dirs, files in os.walk(ssh_dir):
        for d in dirs:
            os.chmod(os.path.join(root, d), 0o700)
        for f in files:
            if f.startswith('id_') and not f.endswith('.pub'):
                os.chmod(os.path.join(root, f), 0o600)
    print("  ✓ Restored SSH configuration")
    restored.append("SSH config")
    return restored


def _print_restore_summary(installed_apps, restored_items):
    print("\n" + "=" * 60)
    print("RESTORE COMPLETE")
    print("=" * 60)
    if installed_apps:
        print(f"\nInstalled {len(installed_apps)} application(s):")
        for app in installed_apps:
            print(f"  ✓ {app}")
    print(f"\nSuccessfully restored {len(restored_items)} item(s):")
    for item in restored_items:
        print(f"  ✓ {item}")
    print("\n⚠ Restart any restored applications for changes to take effect.")
