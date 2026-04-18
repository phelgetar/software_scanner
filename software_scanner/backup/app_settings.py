#!/usr/bin/env python3
#
###################################################################
# Project: software_scanner
# File: software_scanner/backup/app_settings.py
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

from software_scanner.utils import format_size


_APPS_WITH_SESSIONS = {
    'BBEdit': 'BBEdit (TextWrangler) - sessions, unsaved files, open documents',
    'TextWrangler': 'TextWrangler - sessions and open files',
    'Sublime Text': 'Sublime Text - sessions, unsaved buffers',
    'Sublime Text 2': 'Sublime Text 2 - sessions',
    'Sublime Text 3': 'Sublime Text 3 - sessions',
    'Atom': 'Atom - sessions and unsaved files',
    'TextMate': 'TextMate - sessions',
    'MacVim': 'MacVim - sessions',
    'Code': 'VS Code - workspace state',
    'iTerm2': 'iTerm2 - sessions and arrangements',
    'Terminal': 'Terminal - saved sessions',
    'Preview': 'Preview - recently opened files',
    'Skim': 'Skim PDF - sessions',
    'TablePlus': 'TablePlus - connections and sessions',
    'Sequel Pro': 'Sequel Pro - database connections',
    'Sequel Ace': 'Sequel Ace - database connections',
    'Tower': 'Tower Git - repositories',
    'SourceTree': 'SourceTree - repositories',
    'Postman': 'Postman - collections and environments',
    'Notes': 'Apple Notes - notes data',
    'Bear': 'Bear - notes',
    'Notion': 'Notion - local cache',
    'Obsidian': 'Obsidian - vaults',
    'Slack': 'Slack - workspace data',
    'Discord': 'Discord - settings',
    'Spotify': 'Spotify - preferences',
    'Adobe': 'Adobe apps - preferences',
    'JetBrains': 'JetBrains IDEs - settings',
    'IntelliJIdea': 'IntelliJ IDEA - settings',
    'PyCharm': 'PyCharm - settings',
    'WebStorm': 'WebStorm - settings',
    'PhpStorm': 'PhpStorm - settings',
    'RubyMine': 'RubyMine - settings',
    'GoLand': 'GoLand - settings',
    'DataGrip': 'DataGrip - settings',
    'CLion': 'CLion - settings',
}

_IMPORTANT_CONTAINERS = [
    'com.apple.TextEdit',
    'com.apple.Notes',
    'com.apple.Pages',
    'com.apple.Numbers',
    'com.apple.Keynote',
    'com.barebones.bbedit',
    'com.coteditor.CotEditor',
]

_SHELL_FILES = ['.bashrc', '.bash_profile', '.zshrc', '.zprofile', '.profile']


def backup_application_settings(backup_dir):
    """Backup preferences, app support data, SSH, Git config, and shell profiles"""
    print("\nBacking up application settings...")
    settings_dir = os.path.join(backup_dir, 'Application_Settings')
    os.makedirs(settings_dir, exist_ok=True)

    pref_count = _backup_preferences(settings_dir)
    apps_backed_up = _backup_app_support(settings_dir)
    _backup_saved_states(settings_dir)
    _backup_containers(settings_dir)
    _backup_dotfiles(settings_dir)
    _backup_vscode(settings_dir)

    return {
        'preference_files': pref_count,
        'apps_with_sessions': apps_backed_up,
    }


def _backup_preferences(settings_dir):
    prefs_dir = os.path.expanduser("~/Library/Preferences")
    prefs_backup_dir = os.path.join(settings_dir, 'Preferences')
    os.makedirs(prefs_backup_dir, exist_ok=True)
    count = 0
    if os.path.exists(prefs_dir):
        print("  Backing up application preferences...")
        for filename in os.listdir(prefs_dir):
            if filename.endswith('.plist'):
                src = os.path.join(prefs_dir, filename)
                if os.path.isfile(src):
                    try:
                        shutil.copy2(src, os.path.join(prefs_backup_dir, filename))
                        count += 1
                    except Exception:
                        pass
        print(f"    ✓ Backed up {count} preference files")
    return count


def _backup_app_support(settings_dir):
    print("\n  Backing up Application Support folders (sessions & app data)...")
    app_support_dir = os.path.expanduser("~/Library/Application Support")
    app_support_backup_dir = os.path.join(settings_dir, 'Application_Support')
    os.makedirs(app_support_backup_dir, exist_ok=True)
    apps_backed_up = []

    if not os.path.exists(app_support_dir):
        return apps_backed_up

    for app_folder in os.listdir(app_support_dir):
        if app_folder not in _APPS_WITH_SESSIONS:
            continue
        app_path = os.path.join(app_support_dir, app_folder)
        if not os.path.isdir(app_path):
            continue
        dest_path = os.path.join(app_support_backup_dir, app_folder)
        try:
            print(f"    Backing up: {app_folder}...")
            shutil.copytree(app_path, dest_path, dirs_exist_ok=True)
            total_size = sum(
                os.path.getsize(os.path.join(dp, fn))
                for dp, _, fns in os.walk(dest_path)
                for fn in fns
            )
            apps_backed_up.append({
                'app': app_folder,
                'description': _APPS_WITH_SESSIONS[app_folder],
                'size': total_size,
            })
            print(f"      ✓ {_APPS_WITH_SESSIONS[app_folder]} ({format_size(total_size)})")
        except Exception as e:
            print(f"      ✗ Error backing up {app_folder}: {e}")

    return apps_backed_up


def _backup_saved_states(settings_dir):
    saved_state_dir = os.path.expanduser("~/Library/Saved Application State")
    if not os.path.exists(saved_state_dir):
        return
    print("\n  Backing up Saved Application States (window positions, unsaved data)...")
    state_backup_dir = os.path.join(settings_dir, 'Saved_Application_State')
    try:
        shutil.copytree(saved_state_dir, state_backup_dir, dirs_exist_ok=True)
        count = len([d for d in os.listdir(state_backup_dir)
                     if os.path.isdir(os.path.join(state_backup_dir, d))])
        print(f"    ✓ Backed up {count} application states")
    except Exception as e:
        print(f"    ✗ Error backing up application states: {e}")


def _backup_containers(settings_dir):
    containers_dir = os.path.expanduser("~/Library/Containers")
    if not os.path.exists(containers_dir):
        return
    print("\n  Backing up App Containers (sandboxed application data)...")
    containers_backup_dir = os.path.join(settings_dir, 'Containers')
    os.makedirs(containers_backup_dir, exist_ok=True)
    count = 0
    for container in os.listdir(containers_dir):
        container_path = os.path.join(containers_dir, container)
        if not os.path.isdir(container_path):
            continue
        try:
            shutil.copytree(container_path, os.path.join(containers_backup_dir, container),
                            dirs_exist_ok=True)
            count += 1
        except Exception:
            pass
    print(f"    ✓ Backed up {count} app containers")


def _backup_dotfiles(settings_dir):
    ssh_dir = os.path.expanduser("~/.ssh")
    if os.path.exists(ssh_dir):
        try:
            shutil.copytree(ssh_dir, os.path.join(settings_dir, 'SSH'), dirs_exist_ok=True)
            print("\n    ✓ Backed up SSH configuration")
        except Exception as e:
            print(f"\n    ✗ Error backing up SSH: {e}")

    git_config = os.path.expanduser("~/.gitconfig")
    if os.path.exists(git_config):
        try:
            shutil.copy2(git_config, os.path.join(settings_dir, 'gitconfig'))
            print("    ✓ Backed up Git configuration")
        except Exception as e:
            print(f"    ✗ Error backing up Git config: {e}")

    for shell_file in _SHELL_FILES:
        shell_path = os.path.expanduser(f"~/{shell_file}")
        if os.path.exists(shell_path):
            try:
                shutil.copy2(shell_path, os.path.join(settings_dir, shell_file))
                print(f"    ✓ Backed up {shell_file}")
            except Exception:
                pass


def _backup_vscode(settings_dir):
    vscode_dir = os.path.expanduser("~/Library/Application Support/Code")
    if not os.path.exists(vscode_dir):
        return
    vscode_backup = os.path.join(settings_dir, 'VSCode')
    os.makedirs(vscode_backup, exist_ok=True)
    user_dir = os.path.join(vscode_dir, 'User')
    if os.path.exists(user_dir):
        try:
            shutil.copytree(user_dir, os.path.join(vscode_backup, 'User'), dirs_exist_ok=True)
            print("    ✓ Backed up VS Code settings")
        except Exception as e:
            print(f"    ✗ Error backing up VS Code: {e}")
