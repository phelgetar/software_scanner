#!/usr/bin/env python3
#
###################################################################
# Project: software_scanner
# File: software_scanner/restore/installer.py
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
import subprocess

from software_scanner.utils import run_command


_INSTALL_METHODS = {
    'Google Chrome': {'method': 'cask', 'package': 'google-chrome'},
    'Firefox': {'method': 'cask', 'package': 'firefox'},
    'Brave': {'method': 'cask', 'package': 'brave-browser'},
    'Edge': {'method': 'cask', 'package': 'microsoft-edge'},
    'Opera': {'method': 'cask', 'package': 'opera'},
    'BBEdit': {'method': 'cask', 'package': 'bbedit'},
    'Sublime Text': {'method': 'cask', 'package': 'sublime-text'},
    'Atom': {'method': 'cask', 'package': 'atom'},
    'Visual Studio Code': {'method': 'cask', 'package': 'visual-studio-code'},
    'Code': {'method': 'cask', 'package': 'visual-studio-code'},
    'TextMate': {'method': 'cask', 'package': 'textmate'},
    'MacVim': {'method': 'cask', 'package': 'macvim'},
    'iTerm': {'method': 'cask', 'package': 'iterm2'},
    'iTerm2': {'method': 'cask', 'package': 'iterm2'},
    'TablePlus': {'method': 'cask', 'package': 'tableplus'},
    'Sequel Pro': {'method': 'cask', 'package': 'sequel-pro'},
    'Sequel Ace': {'method': 'cask', 'package': 'sequel-ace'},
    'Postman': {'method': 'cask', 'package': 'postman'},
    'Docker': {'method': 'cask', 'package': 'docker'},
    'Slack': {'method': 'cask', 'package': 'slack'},
    'Discord': {'method': 'cask', 'package': 'discord'},
    'Zoom': {'method': 'cask', 'package': 'zoom'},
    'IntelliJ IDEA': {'method': 'cask', 'package': 'intellij-idea'},
    'PyCharm': {'method': 'cask', 'package': 'pycharm'},
    'WebStorm': {'method': 'cask', 'package': 'webstorm'},
    'PhpStorm': {'method': 'cask', 'package': 'phpstorm'},
    'RubyMine': {'method': 'cask', 'package': 'rubymine'},
    'GoLand': {'method': 'cask', 'package': 'goland'},
    'DataGrip': {'method': 'cask', 'package': 'datagrip'},
    'CLion': {'method': 'cask', 'package': 'clion'},
    'Obsidian': {'method': 'cask', 'package': 'obsidian'},
    'Notion': {'method': 'cask', 'package': 'notion'},
    'Bear': {'method': 'cask', 'package': 'bear'},
    'Tower': {'method': 'cask', 'package': 'tower'},
    'SourceTree': {'method': 'cask', 'package': 'sourcetree'},
}

_APP_NAME_MAPPING = {
    'BBEdit': 'BBEdit', 'TextWrangler': 'BBEdit',
    'Sublime Text': 'Sublime Text', 'Sublime Text 2': 'Sublime Text',
    'Sublime Text 3': 'Sublime Text', 'Atom': 'Atom',
    'Code': 'Visual Studio Code', 'iTerm2': 'iTerm2',
    'Postman': 'Postman', 'Obsidian': 'Obsidian',
    'Notion': 'Notion', 'Bear': 'Bear', 'TablePlus': 'TablePlus',
    'Sequel Pro': 'Sequel Pro', 'Sequel Ace': 'Sequel Ace',
    'Tower': 'Tower', 'SourceTree': 'SourceTree',
    'Slack': 'Slack', 'Discord': 'Discord',
    'IntelliJIdea': 'IntelliJ IDEA', 'PyCharm': 'PyCharm',
    'WebStorm': 'WebStorm', 'PhpStorm': 'PhpStorm',
    'RubyMine': 'RubyMine', 'GoLand': 'GoLand',
    'DataGrip': 'DataGrip', 'CLion': 'CLion',
}


def get_installation_method(app_name):
    return _INSTALL_METHODS.get(app_name)


def is_homebrew_installed():
    result = run_command("which brew")
    return bool(result) and not result.startswith("Error")


def install_homebrew():
    print("\n  Homebrew is not installed. Homebrew is needed to install applications.")
    response = input("  Would you like to install Homebrew? (y/n): ").strip().lower()
    if response != 'y':
        return False
    print("\n  Installing Homebrew...")
    install_cmd = (
        '/bin/bash -c "$(curl -fsSL '
        'https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
    )
    result = subprocess.run(install_cmd, shell=True)
    if result.returncode == 0:
        print("  ✓ Homebrew installed successfully!")
        return True
    print("  ✗ Failed to install Homebrew")
    return False


def install_application(app_name, install_info):
    """Install an application via Homebrew cask"""
    if install_info['method'] != 'cask':
        return False

    if not is_homebrew_installed() and not install_homebrew():
        print(f"\n  Cannot auto-install {app_name} without Homebrew.")
        return False

    print(f"\n  Installing {app_name} via Homebrew...")
    result = subprocess.run(
        f"brew install --cask {install_info['package']}", shell=True
    )
    if result.returncode == 0:
        print(f"  ✓ {app_name} installed successfully!")
        return True
    print(f"  ✗ Failed to install {app_name}")
    return False


def check_if_installed(item_name, item_type):
    """Check whether an application is currently installed"""
    browser_paths = {
        'Chrome': os.path.expanduser("~/Library/Application Support/Google/Chrome"),
        'Firefox': os.path.expanduser("~/Library/Application Support/Firefox"),
        'Brave': os.path.expanduser("~/Library/Application Support/BraveSoftware/Brave-Browser"),
        'Edge': os.path.expanduser("~/Library/Application Support/Microsoft Edge"),
        'Opera': os.path.expanduser("~/Library/Application Support/com.operasoftware.Opera"),
    }
    if item_type in browser_paths:
        return os.path.exists(browser_paths[item_type])
    if item_type == 'Safari':
        return True
    if item_type == 'Application':
        return (
            os.path.exists(f"/Applications/{item_name}.app")
            or os.path.exists(os.path.expanduser(f"~/Applications/{item_name}.app"))
        )
    return True


def analyze_backup_and_offer_installation(backup_dir):
    """Scan backup, identify missing apps, and offer to install them"""
    print("\n" + "=" * 60)
    print("CHECKING FOR MISSING SOFTWARE")
    print("=" * 60)

    missing_apps = _find_missing_apps(backup_dir)

    if not missing_apps:
        print("✓ All applications from the backup are already installed!")
        return []

    print(f"Found {len(missing_apps)} missing application(s):\n")
    for i, app in enumerate(missing_apps, 1):
        info = get_installation_method(app)
        status = "Can auto-install" if info else "Manual install needed"
        print(f"  {i}. {app} - {status}")

    print()
    print("Would you like to install the missing applications?")
    print("  1. Install all automatically (where possible)")
    print("  2. Choose which ones to install")
    print("  3. Skip installation")

    while True:
        choice = input("\nEnter your choice (1-3): ").strip()
        if choice in ['1', '2', '3']:
            break
        print("Invalid choice. Please enter 1, 2, or 3.")

    if choice == '3':
        return []

    apps_to_install = missing_apps if choice == '1' else _select_apps(missing_apps)

    installed = []
    print("\n" + "=" * 60)
    print("INSTALLING APPLICATIONS")
    print("=" * 60)
    for app_name in apps_to_install:
        print(f"\n▶ Installing {app_name}...")
        info = get_installation_method(app_name)
        if info and install_application(app_name, info):
            installed.append(app_name)
        elif not info:
            print(f"  ⚠ No automatic installation method available for {app_name}")

    if installed:
        print("\n" + "=" * 60)
        print(f"Successfully installed {len(installed)} application(s):")
        for app in installed:
            print(f"  ✓ {app}")
        print("=" * 60)

    return installed


def _find_missing_apps(backup_dir):
    missing = []

    browser_checks = {
        'Google Chrome': ('Google_Chrome', 'Chrome'),
        'Firefox': ('Firefox_Backup', 'Firefox'),
        'Brave': ('Brave_Backup', 'Brave'),
        'Edge': ('Edge_Backup', 'Edge'),
        'Opera': ('Opera_Backup', 'Opera'),
    }
    for app_name, (folder, check_type) in browser_checks.items():
        if os.path.exists(os.path.join(backup_dir, folder)):
            if not check_if_installed(app_name, check_type):
                missing.append(app_name)

    app_support_backup = os.path.join(backup_dir, 'Application_Settings', 'Application_Support')
    if os.path.exists(app_support_backup):
        for folder in os.listdir(app_support_backup):
            app_name = _APP_NAME_MAPPING.get(folder)
            if app_name and not check_if_installed(app_name, 'Application'):
                if app_name not in missing:
                    missing.append(app_name)

    return missing


def _select_apps(missing_apps):
    print("\nSelect applications to install (comma-separated numbers, e.g., 1,3):")
    selection = input("Your selection: ").strip()
    try:
        indices = [int(x.strip()) for x in selection.split(',')]
        return [missing_apps[i - 1] for i in indices if 1 <= i <= len(missing_apps)]
    except Exception:
        print("Invalid selection. Skipping installation.")
        return []
