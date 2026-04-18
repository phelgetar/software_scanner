#!/usr/bin/env python3
"""
macOS Software Scanner & Profile Backup Tool
Scans and documents all installed software with versions on macOS
Creates backups of Chrome profiles, bookmarks, cookies, and settings
"""

import subprocess
import json
import csv
import os
import shutil
from datetime import datetime
from pathlib import Path

def run_command(command):
    """Run a shell command and return output"""
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.stdout.strip()
    except Exception as e:
        return f"Error: {str(e)}"

def get_applications():
    """Get all applications from /Applications and ~/Applications"""
    apps = []
    
    # System applications
    system_apps_path = "/Applications"
    # User applications
    user_apps_path = os.path.expanduser("~/Applications")
    
    for apps_path in [system_apps_path, user_apps_path]:
        if os.path.exists(apps_path):
            for item in os.listdir(apps_path):
                if item.endswith('.app'):
                    app_path = os.path.join(apps_path, item)
                    app_name = item.replace('.app', '')
                    
                    # Get version from Info.plist
                    plist_path = os.path.join(app_path, 'Contents', 'Info.plist')
                    version = get_app_version(plist_path)
                    
                    apps.append({
                        'name': app_name,
                        'version': version,
                        'path': app_path,
                        'type': 'Application'
                    })
    
    return apps

def get_app_version(plist_path):
    """Extract version from Info.plist"""
    if not os.path.exists(plist_path):
        return "Unknown"
    
    try:
        # Use defaults or PlistBuddy to read the plist
        cmd = f"defaults read '{plist_path.replace('/Info.plist', '')}' CFBundleShortVersionString 2>/dev/null"
        version = run_command(cmd)
        
        if not version or version.startswith("Error"):
            # Try alternative version key
            cmd = f"defaults read '{plist_path.replace('/Info.plist', '')}' CFBundleVersion 2>/dev/null"
            version = run_command(cmd)
        
        return version if version and not version.startswith("Error") else "Unknown"
    except:
        return "Unknown"

def get_homebrew_packages():
    """Get Homebrew installed packages"""
    packages = []
    
    # Check if Homebrew is installed
    brew_check = run_command("which brew")
    if not brew_check or brew_check.startswith("Error"):
        return packages
    
    # Get installed formulae
    formulae = run_command("brew list --formula --versions")
    if formulae and not formulae.startswith("Error"):
        for line in formulae.split('\n'):
            if line.strip():
                parts = line.strip().split(' ', 1)
                if len(parts) == 2:
                    packages.append({
                        'name': parts[0],
                        'version': parts[1],
                        'path': 'Homebrew',
                        'type': 'Homebrew Formula'
                    })
    
    # Get installed casks
    casks = run_command("brew list --cask --versions")
    if casks and not casks.startswith("Error"):
        for line in casks.split('\n'):
            if line.strip():
                parts = line.strip().split(' ', 1)
                if len(parts) == 2:
                    packages.append({
                        'name': parts[0],
                        'version': parts[1],
                        'path': 'Homebrew',
                        'type': 'Homebrew Cask'
                    })
    
    return packages

def get_system_profile_apps():
    """Get applications using system_profiler"""
    apps = []
    
    cmd = "system_profiler SPApplicationsDataType -json"
    output = run_command(cmd)
    
    if output and not output.startswith("Error"):
        try:
            data = json.loads(output)
            if 'SPApplicationsDataType' in data:
                for app in data['SPApplicationsDataType']:
                    apps.append({
                        'name': app.get('_name', 'Unknown'),
                        'version': app.get('version', 'Unknown'),
                        'path': app.get('path', 'Unknown'),
                        'type': 'System Profile'
                    })
        except json.JSONDecodeError:
            pass
    
    return apps

def get_python_packages():
    """Get installed Python packages"""
    packages = []
    
    # Try pip3 first, then pip
    for pip_cmd in ['pip3', 'pip']:
        output = run_command(f"{pip_cmd} list --format=json 2>/dev/null")
        if output and not output.startswith("Error"):
            try:
                pip_packages = json.loads(output)
                for pkg in pip_packages:
                    packages.append({
                        'name': pkg.get('name', 'Unknown'),
                        'version': pkg.get('version', 'Unknown'),
                        'path': f'Python ({pip_cmd})',
                        'type': 'Python Package'
                    })
                break  # Only use one pip command
            except json.JSONDecodeError:
                continue
    
    return packages

def get_npm_packages():
    """Get globally installed npm packages"""
    packages = []
    
    output = run_command("npm list -g --depth=0 --json 2>/dev/null")
    if output and not output.startswith("Error"):
        try:
            data = json.loads(output)
            dependencies = data.get('dependencies', {})
            for name, info in dependencies.items():
                packages.append({
                    'name': name,
                    'version': info.get('version', 'Unknown'),
                    'path': 'npm (global)',
                    'type': 'npm Package'
                })
        except json.JSONDecodeError:
            pass
    
    return packages

def backup_chrome_profiles(backup_dir):
    """Backup Chrome profiles including bookmarks, cookies, and settings"""
    print("\nBacking up Chrome profiles...")
    
    chrome_paths = [
        os.path.expanduser("~/Library/Application Support/Google/Chrome"),
        os.path.expanduser("~/Library/Application Support/Google/Chrome Canary"),
        os.path.expanduser("~/Library/Application Support/Chromium"),
    ]
    
    backup_info = {
        'timestamp': datetime.now().isoformat(),
        'profiles': []
    }
    
    for chrome_path in chrome_paths:
        if not os.path.exists(chrome_path):
            continue
        
        browser_name = os.path.basename(chrome_path)
        browser_backup_dir = os.path.join(backup_dir, browser_name.replace(' ', '_'))
        os.makedirs(browser_backup_dir, exist_ok=True)
        
        print(f"\n  Processing {browser_name}...")
        
        # Backup Local State (browser-wide settings)
        local_state_path = os.path.join(chrome_path, 'Local State')
        if os.path.exists(local_state_path):
            try:
                shutil.copy2(local_state_path, os.path.join(browser_backup_dir, 'Local_State.json'))
                print(f"    ✓ Backed up Local State")
            except Exception as e:
                print(f"    ✗ Error backing up Local State: {e}")
        
        # Find all profiles
        profiles_found = []
        for item in os.listdir(chrome_path):
            profile_path = os.path.join(chrome_path, item)
            
            # Check if this is a profile directory
            if os.path.isdir(profile_path) and (item.startswith('Profile ') or item == 'Default'):
                profiles_found.append((item, profile_path))
        
        print(f"    Found {len(profiles_found)} profile(s)")
        
        for profile_name, profile_path in profiles_found:
            print(f"\n    Backing up profile: {profile_name}")
            profile_backup_dir = os.path.join(browser_backup_dir, profile_name.replace(' ', '_'))
            os.makedirs(profile_backup_dir, exist_ok=True)
            
            profile_info = {
                'name': profile_name,
                'browser': browser_name,
                'backed_up_items': []
            }
            
            # Files to backup
            files_to_backup = {
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
            
            for source_name, dest_name in files_to_backup.items():
                source_path = os.path.join(profile_path, source_name)
                if os.path.exists(source_path):
                    try:
                        dest_path = os.path.join(profile_backup_dir, dest_name)
                        shutil.copy2(source_path, dest_path)
                        file_size = os.path.getsize(source_path)
                        profile_info['backed_up_items'].append({
                            'file': source_name,
                            'size_bytes': file_size
                        })
                        print(f"      ✓ {source_name} ({format_size(file_size)})")
                    except Exception as e:
                        print(f"      ✗ Error backing up {source_name}: {e}")
            
            # Backup Extensions directory
            extensions_path = os.path.join(profile_path, 'Extensions')
            if os.path.exists(extensions_path):
                try:
                    extensions_backup = os.path.join(profile_backup_dir, 'Extensions')
                    shutil.copytree(extensions_path, extensions_backup, dirs_exist_ok=True)
                    
                    # Count extensions
                    extension_count = len([d for d in os.listdir(extensions_path) 
                                         if os.path.isdir(os.path.join(extensions_path, d))])
                    profile_info['extension_count'] = extension_count
                    print(f"      ✓ Extensions folder ({extension_count} extension(s))")
                except Exception as e:
                    print(f"      ✗ Error backing up Extensions: {e}")
            
            # Backup Storage (for extension data, cache, etc.)
            storage_path = os.path.join(profile_path, 'Storage')
            if os.path.exists(storage_path):
                try:
                    storage_backup = os.path.join(profile_backup_dir, 'Storage')
                    shutil.copytree(storage_path, storage_backup, dirs_exist_ok=True)
                    print(f"      ✓ Storage folder")
                except Exception as e:
                    print(f"      ✗ Error backing up Storage: {e}")
            
            # Backup Sessions directory (contains tab session data)
            sessions_path = os.path.join(profile_path, 'Sessions')
            if os.path.exists(sessions_path):
                try:
                    sessions_backup = os.path.join(profile_backup_dir, 'Sessions')
                    shutil.copytree(sessions_path, sessions_backup, dirs_exist_ok=True)
                    print(f"      ✓ Sessions folder (tab restore data)")
                except Exception as e:
                    print(f"      ✗ Error backing up Sessions: {e}")
            
            # Extract and display open tabs information if available
            try:
                current_tabs_path = os.path.join(profile_path, 'Current Tabs')
                if os.path.exists(current_tabs_path):
                    tab_count = extract_tab_count(current_tabs_path)
                    if tab_count:
                        profile_info['current_open_tabs'] = tab_count
                        print(f"      ℹ Currently has {tab_count} open tab(s)")
            except Exception as e:
                pass  # Tab extraction is optional
            
            backup_info['profiles'].append(profile_info)
    
    # Save backup manifest
    manifest_path = os.path.join(backup_dir, 'backup_manifest.json')
    with open(manifest_path, 'w') as f:
        json.dump(backup_info, f, indent=2)
    
    print(f"\n  Backup manifest saved to: {manifest_path}")
    return backup_info

def backup_other_browser_profiles(backup_dir):
    """Backup profiles from other browsers"""
    print("\nBacking up other browser profiles...")
    
    browser_configs = {
        'Firefox': os.path.expanduser("~/Library/Application Support/Firefox/Profiles"),
        'Safari': os.path.expanduser("~/Library/Safari"),
        'Brave': os.path.expanduser("~/Library/Application Support/BraveSoftware/Brave-Browser"),
        'Edge': os.path.expanduser("~/Library/Application Support/Microsoft Edge"),
        'Opera': os.path.expanduser("~/Library/Application Support/com.operasoftware.Opera"),
    }
    
    backed_up = []
    
    for browser_name, browser_path in browser_configs.items():
        if os.path.exists(browser_path):
            print(f"\n  Processing {browser_name}...")
            browser_backup_dir = os.path.join(backup_dir, f"{browser_name}_Backup")
            
            try:
                # For Firefox, copy the entire Profiles directory
                if browser_name == 'Firefox':
                    shutil.copytree(browser_path, browser_backup_dir, dirs_exist_ok=True)
                    print(f"    ✓ Backed up Firefox profiles")
                    backed_up.append(browser_name)
                
                # For Safari, backup key files
                elif browser_name == 'Safari':
                    os.makedirs(browser_backup_dir, exist_ok=True)
                    safari_files = ['Bookmarks.plist', 'History.db', 'Cookies.binarycookies', 
                                   'Downloads.plist', 'LastSession.plist', 'TopSites.plist']
                    for filename in safari_files:
                        src = os.path.join(browser_path, filename)
                        if os.path.exists(src):
                            shutil.copy2(src, os.path.join(browser_backup_dir, filename))
                            print(f"    ✓ {filename}")
                    backed_up.append(browser_name)
                
                # For Chromium-based browsers (Brave, Edge, Opera)
                else:
                    # Use similar logic as Chrome
                    shutil.copytree(browser_path, browser_backup_dir, dirs_exist_ok=True)
                    print(f"    ✓ Backed up {browser_name} profiles")
                    backed_up.append(browser_name)
                    
            except Exception as e:
                print(f"    ✗ Error backing up {browser_name}: {e}")
    
    return backed_up

def backup_application_settings(backup_dir):
    """Backup common application settings and preferences"""
    print("\nBacking up application settings...")
    
    settings_backup_dir = os.path.join(backup_dir, 'Application_Settings')
    os.makedirs(settings_backup_dir, exist_ok=True)
    
    # macOS Preferences
    prefs_dir = os.path.expanduser("~/Library/Preferences")
    prefs_backup_dir = os.path.join(settings_backup_dir, 'Preferences')
    os.makedirs(prefs_backup_dir, exist_ok=True)
    
    backed_up_count = 0
    
    # Backup common application preference files
    if os.path.exists(prefs_dir):
        print("  Backing up application preferences...")
        for filename in os.listdir(prefs_dir):
            if filename.endswith('.plist'):
                try:
                    src = os.path.join(prefs_dir, filename)
                    if os.path.isfile(src):
                        shutil.copy2(src, os.path.join(prefs_backup_dir, filename))
                        backed_up_count += 1
                except Exception as e:
                    pass  # Skip files we can't read
        print(f"    ✓ Backed up {backed_up_count} preference files")
    
    # Backup Application Support folder (contains session data for many apps)
    print("\n  Backing up Application Support folders (sessions & app data)...")
    app_support_dir = os.path.expanduser("~/Library/Application Support")
    app_support_backup_dir = os.path.join(settings_backup_dir, 'Application_Support')
    os.makedirs(app_support_backup_dir, exist_ok=True)
    
    # List of common applications that store session data
    apps_with_sessions = {
        'BBEdit': 'BBEdit (TextWrangler) - sessions, unsaved files, open documents',
        'TextWrangler': 'TextWrangler - sessions and open files',
        'Sublime Text': 'Sublime Text - sessions, unsaved buffers',
        'Sublime Text 2': 'Sublime Text 2 - sessions',
        'Sublime Text 3': 'Sublime Text 3 - sessions',
        'Atom': 'Atom - sessions and unsaved files',
        'TextMate': 'TextMate - sessions',
        'MacVim': 'MacVim - sessions',
        'Code': 'VS Code - workspace state (already covered)',
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
    
    apps_backed_up = []
    
    if os.path.exists(app_support_dir):
        for app_folder in os.listdir(app_support_dir):
            app_path = os.path.join(app_support_dir, app_folder)
            
            # Skip non-directories
            if not os.path.isdir(app_path):
                continue
            
            # Check if this is an app we specifically want to backup
            if app_folder in apps_with_sessions:
                try:
                    dest_path = os.path.join(app_support_backup_dir, app_folder)
                    print(f"    Backing up: {app_folder}...")
                    shutil.copytree(app_path, dest_path, dirs_exist_ok=True)
                    
                    # Calculate size
                    total_size = sum(
                        os.path.getsize(os.path.join(dirpath, filename))
                        for dirpath, dirnames, filenames in os.walk(dest_path)
                        for filename in filenames
                    )
                    
                    apps_backed_up.append({
                        'app': app_folder,
                        'description': apps_with_sessions[app_folder],
                        'size': total_size
                    })
                    print(f"      ✓ {apps_with_sessions[app_folder]} ({format_size(total_size)})")
                except Exception as e:
                    print(f"      ✗ Error backing up {app_folder}: {e}")
    
    # Backup saved application states
    saved_app_state_dir = os.path.expanduser("~/Library/Saved Application State")
    if os.path.exists(saved_app_state_dir):
        print("\n  Backing up Saved Application States (window positions, unsaved data)...")
        state_backup_dir = os.path.join(settings_backup_dir, 'Saved_Application_State')
        try:
            shutil.copytree(saved_app_state_dir, state_backup_dir, dirs_exist_ok=True)
            state_count = len([d for d in os.listdir(state_backup_dir) 
                             if os.path.isdir(os.path.join(state_backup_dir, d))])
            print(f"    ✓ Backed up {state_count} application states")
        except Exception as e:
            print(f"    ✗ Error backing up application states: {e}")
    
    # Backup Containers (sandboxed app data)
    containers_dir = os.path.expanduser("~/Library/Containers")
    if os.path.exists(containers_dir):
        print("\n  Backing up App Containers (sandboxed application data)...")
        containers_backup_dir = os.path.join(settings_backup_dir, 'Containers')
        os.makedirs(containers_backup_dir, exist_ok=True)
        
        # Common sandboxed apps that might have session data
        important_containers = [
            'com.apple.TextEdit',
            'com.apple.Notes',
            'com.apple.Pages',
            'com.apple.Numbers',
            'com.apple.Keynote',
            'com.barebones.bbedit',
            'com.coteditor.CotEditor',
        ]
        
        container_count = 0
        for container in os.listdir(containers_dir):
            container_path = os.path.join(containers_dir, container)
            if not os.path.isdir(container_path):
                continue
            
            # Backup all containers (they're usually small) or filter to important ones
            # For now, let's backup all to be comprehensive
            try:
                dest_path = os.path.join(containers_backup_dir, container)
                shutil.copytree(container_path, dest_path, dirs_exist_ok=True)
                container_count += 1
            except Exception as e:
                pass  # Some containers may be locked
        
        print(f"    ✓ Backed up {container_count} app containers")
    
    # Backup SSH keys and config
    ssh_dir = os.path.expanduser("~/.ssh")
    if os.path.exists(ssh_dir):
        try:
            ssh_backup_dir = os.path.join(settings_backup_dir, 'SSH')
            shutil.copytree(ssh_dir, ssh_backup_dir, dirs_exist_ok=True)
            print("\n    ✓ Backed up SSH configuration")
        except Exception as e:
            print(f"\n    ✗ Error backing up SSH: {e}")
    
    # Backup Git config
    git_config = os.path.expanduser("~/.gitconfig")
    if os.path.exists(git_config):
        try:
            shutil.copy2(git_config, os.path.join(settings_backup_dir, 'gitconfig'))
            print("    ✓ Backed up Git configuration")
        except Exception as e:
            print(f"    ✗ Error backing up Git config: {e}")
    
    # Backup shell profiles
    shell_files = ['.bashrc', '.bash_profile', '.zshrc', '.zprofile', '.profile']
    for shell_file in shell_files:
        shell_path = os.path.expanduser(f"~/{shell_file}")
        if os.path.exists(shell_path):
            try:
                shutil.copy2(shell_path, os.path.join(settings_backup_dir, shell_file))
                print(f"    ✓ Backed up {shell_file}")
            except Exception as e:
                pass
    
    # Backup VS Code settings if exists
    vscode_dir = os.path.expanduser("~/Library/Application Support/Code")
    if os.path.exists(vscode_dir):
        try:
            vscode_backup = os.path.join(settings_backup_dir, 'VSCode')
            os.makedirs(vscode_backup, exist_ok=True)
            
            # Backup user settings
            user_dir = os.path.join(vscode_dir, 'User')
            if os.path.exists(user_dir):
                user_backup = os.path.join(vscode_backup, 'User')
                shutil.copytree(user_dir, user_backup, dirs_exist_ok=True)
                print("    ✓ Backed up VS Code settings")
        except Exception as e:
            print(f"    ✗ Error backing up VS Code: {e}")
    
    return {
        'preference_files': backed_up_count,
        'apps_with_sessions': apps_backed_up
    }

def format_size(bytes_size):
    """Format bytes to human readable size"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f} TB"

def extract_tab_count(tabs_file_path):
    """Extract approximate tab count from Current Tabs file"""
    try:
        with open(tabs_file_path, 'rb') as f:
            content = f.read()
            # Count occurrences of URL patterns (rough estimate)
            tab_count = content.count(b'http://') + content.count(b'https://')
            return tab_count if tab_count > 0 else None
    except:
        return None

def find_backup_directories():
    """Find all backup directories in current location"""
    backups = []
    for item in os.listdir('.'):
        if os.path.isdir(item) and item.startswith('mac_backup_'):
            # Check if it has a backup_summary.json
            summary_path = os.path.join(item, 'backup_summary.json')
            if os.path.exists(summary_path):
                try:
                    with open(summary_path, 'r') as f:
                        summary = json.load(f)
                    backups.append({
                        'directory': item,
                        'timestamp': summary.get('timestamp', 'Unknown'),
                        'summary': summary
                    })
                except:
                    pass
    return sorted(backups, key=lambda x: x['timestamp'], reverse=True)

def check_if_installed(item_name, item_type):
    """Check if software/application is currently installed"""
    if item_type == 'Chrome':
        chrome_path = os.path.expanduser("~/Library/Application Support/Google/Chrome")
        return os.path.exists(chrome_path)
    elif item_type == 'Firefox':
        firefox_path = os.path.expanduser("~/Library/Application Support/Firefox")
        return os.path.exists(firefox_path)
    elif item_type == 'Safari':
        # Safari is built-in to macOS
        return True
    elif item_type == 'Brave':
        brave_path = os.path.expanduser("~/Library/Application Support/BraveSoftware/Brave-Browser")
        return os.path.exists(brave_path)
    elif item_type == 'Edge':
        edge_path = os.path.expanduser("~/Library/Application Support/Microsoft Edge")
        return os.path.exists(edge_path)
    elif item_type == 'Opera':
        opera_path = os.path.expanduser("~/Library/Application Support/com.operasoftware.Opera")
        return os.path.exists(opera_path)
    elif item_type == 'Application':
        # Check if app exists in Applications
        app_path = f"/Applications/{item_name}.app"
        user_app_path = os.path.expanduser(f"~/Applications/{item_name}.app")
        return os.path.exists(app_path) or os.path.exists(user_app_path)
    
    return True  # Assume it's okay to restore if we can't check

def get_installation_method(app_name):
    """Determine how to install an application"""
    # Dictionary mapping applications to their installation methods
    install_methods = {
        # Browsers
        'Google Chrome': {'method': 'cask', 'package': 'google-chrome', 'url': 'https://www.google.com/chrome/'},
        'Firefox': {'method': 'cask', 'package': 'firefox', 'url': 'https://www.mozilla.org/firefox/'},
        'Brave': {'method': 'cask', 'package': 'brave-browser', 'url': 'https://brave.com/'},
        'Edge': {'method': 'cask', 'package': 'microsoft-edge', 'url': 'https://www.microsoft.com/edge'},
        'Opera': {'method': 'cask', 'package': 'opera', 'url': 'https://www.opera.com/'},
        
        # Text Editors & IDEs
        'BBEdit': {'method': 'cask', 'package': 'bbedit', 'url': 'https://www.barebones.com/products/bbedit/'},
        'Sublime Text': {'method': 'cask', 'package': 'sublime-text', 'url': 'https://www.sublimetext.com/'},
        'Atom': {'method': 'cask', 'package': 'atom', 'url': 'https://atom.io/'},
        'Visual Studio Code': {'method': 'cask', 'package': 'visual-studio-code', 'url': 'https://code.visualstudio.com/'},
        'Code': {'method': 'cask', 'package': 'visual-studio-code', 'url': 'https://code.visualstudio.com/'},
        'TextMate': {'method': 'cask', 'package': 'textmate', 'url': 'https://macromates.com/'},
        'MacVim': {'method': 'cask', 'package': 'macvim', 'url': 'https://macvim.org/'},
        
        # Terminals
        'iTerm': {'method': 'cask', 'package': 'iterm2', 'url': 'https://iterm2.com/'},
        'iTerm2': {'method': 'cask', 'package': 'iterm2', 'url': 'https://iterm2.com/'},
        
        # Database Tools
        'TablePlus': {'method': 'cask', 'package': 'tableplus', 'url': 'https://tableplus.com/'},
        'Sequel Pro': {'method': 'cask', 'package': 'sequel-pro', 'url': 'https://www.sequelpro.com/'},
        'Sequel Ace': {'method': 'cask', 'package': 'sequel-ace', 'url': 'https://sequel-ace.com/'},
        
        # Developer Tools
        'Postman': {'method': 'cask', 'package': 'postman', 'url': 'https://www.postman.com/'},
        'Docker': {'method': 'cask', 'package': 'docker', 'url': 'https://www.docker.com/'},
        'Slack': {'method': 'cask', 'package': 'slack', 'url': 'https://slack.com/'},
        'Discord': {'method': 'cask', 'package': 'discord', 'url': 'https://discord.com/'},
        'Zoom': {'method': 'cask', 'package': 'zoom', 'url': 'https://zoom.us/'},
        
        # JetBrains IDEs
        'IntelliJ IDEA': {'method': 'cask', 'package': 'intellij-idea', 'url': 'https://www.jetbrains.com/idea/'},
        'PyCharm': {'method': 'cask', 'package': 'pycharm', 'url': 'https://www.jetbrains.com/pycharm/'},
        'WebStorm': {'method': 'cask', 'package': 'webstorm', 'url': 'https://www.jetbrains.com/webstorm/'},
        'PhpStorm': {'method': 'cask', 'package': 'phpstorm', 'url': 'https://www.jetbrains.com/phpstorm/'},
        'RubyMine': {'method': 'cask', 'package': 'rubymine', 'url': 'https://www.jetbrains.com/ruby/'},
        'GoLand': {'method': 'cask', 'package': 'goland', 'url': 'https://www.jetbrains.com/go/'},
        'DataGrip': {'method': 'cask', 'package': 'datagrip', 'url': 'https://www.jetbrains.com/datagrip/'},
        'CLion': {'method': 'cask', 'package': 'clion', 'url': 'https://www.jetbrains.com/clion/'},
        
        # Note Apps
        'Obsidian': {'method': 'cask', 'package': 'obsidian', 'url': 'https://obsidian.md/'},
        'Notion': {'method': 'cask', 'package': 'notion', 'url': 'https://www.notion.so/'},
        'Bear': {'method': 'cask', 'package': 'bear', 'url': 'https://bear.app/'},
        
        # Git Clients
        'Tower': {'method': 'cask', 'package': 'tower', 'url': 'https://www.git-tower.com/'},
        'SourceTree': {'method': 'cask', 'package': 'sourcetree', 'url': 'https://www.sourcetreeapp.com/'},
    }
    
    return install_methods.get(app_name, None)

def check_homebrew_installed():
    """Check if Homebrew is installed"""
    result = run_command("which brew")
    return result and not result.startswith("Error") and len(result) > 0

def install_homebrew():
    """Install Homebrew"""
    print("\n  Homebrew is not installed. Homebrew is needed to install applications.")
    print("  Homebrew is a free, open-source package manager for macOS.")
    response = input("  Would you like to install Homebrew? (y/n): ").strip().lower()
    
    if response != 'y':
        return False
    
    print("\n  Installing Homebrew...")
    print("  This may take several minutes and will require your password.")
    
    install_cmd = '/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
    result = subprocess.run(install_cmd, shell=True)
    
    if result.returncode == 0:
        print("  ✓ Homebrew installed successfully!")
        return True
    else:
        print("  ✗ Failed to install Homebrew")
        return False

def install_application(app_name, install_info):
    """Install an application using Homebrew or provide download URL"""
    if install_info['method'] == 'cask':
        # Check if Homebrew is installed
        if not check_homebrew_installed():
            if not install_homebrew():
                print(f"\n  Cannot auto-install {app_name} without Homebrew.")
                print(f"  You can manually download from: {install_info['url']}")
                return False
        
        print(f"\n  Installing {app_name} via Homebrew...")
        install_cmd = f"brew install --cask {install_info['package']}"
        
        result = subprocess.run(install_cmd, shell=True)
        
        if result.returncode == 0:
            print(f"  ✓ {app_name} installed successfully!")
            return True
        else:
            print(f"  ✗ Failed to install {app_name}")
            print(f"  You can manually download from: {install_info['url']}")
            return False
    
    elif install_info['method'] == 'url':
        print(f"\n  {app_name} must be downloaded manually.")
        print(f"  Download URL: {install_info['url']}")
        response = input("  Open URL in browser? (y/n): ").strip().lower()
        if response == 'y':
            subprocess.run(f"open '{install_info['url']}'", shell=True)
        return False
    
    return False

def analyze_backup_and_offer_installation(backup_dir):
    """Analyze backup to find missing software and offer installation"""
    print("\n" + "=" * 60)
    print("CHECKING FOR MISSING SOFTWARE")
    print("=" * 60)
    print()
    
    missing_apps = []
    
    # Check browsers
    browser_checks = {
        'Google Chrome': ('Google_Chrome', 'Chrome'),
        'Firefox': ('Firefox_Backup', 'Firefox'),
        'Brave': ('Brave_Backup', 'Brave'),
        'Edge': ('Edge_Backup', 'Edge'),
        'Opera': ('Opera_Backup', 'Opera'),
    }
    
    for app_name, (backup_folder, check_type) in browser_checks.items():
        backup_path = os.path.join(backup_dir, backup_folder)
        if os.path.exists(backup_path):
            if not check_if_installed(app_name, check_type):
                missing_apps.append(app_name)
    
    # Check applications with backed up data
    app_support_backup = os.path.join(backup_dir, 'Application_Settings', 'Application_Support')
    if os.path.exists(app_support_backup):
        for app_folder in os.listdir(app_support_backup):
            # Map folder names to proper app names
            app_name_mapping = {
                'BBEdit': 'BBEdit',
                'TextWrangler': 'BBEdit',
                'Sublime Text': 'Sublime Text',
                'Sublime Text 2': 'Sublime Text',
                'Sublime Text 3': 'Sublime Text',
                'Atom': 'Atom',
                'Code': 'Visual Studio Code',
                'iTerm2': 'iTerm2',
                'Postman': 'Postman',
                'Obsidian': 'Obsidian',
                'Notion': 'Notion',
                'Bear': 'Bear',
                'TablePlus': 'TablePlus',
                'Sequel Pro': 'Sequel Pro',
                'Sequel Ace': 'Sequel Ace',
                'Tower': 'Tower',
                'SourceTree': 'SourceTree',
                'Slack': 'Slack',
                'Discord': 'Discord',
                'IntelliJIdea': 'IntelliJ IDEA',
                'PyCharm': 'PyCharm',
                'WebStorm': 'WebStorm',
                'PhpStorm': 'PhpStorm',
                'RubyMine': 'RubyMine',
                'GoLand': 'GoLand',
                'DataGrip': 'DataGrip',
                'CLion': 'CLion',
            }
            
            if app_folder in app_name_mapping:
                app_name = app_name_mapping[app_folder]
                if not check_if_installed(app_name, 'Application'):
                    if app_name not in missing_apps:
                        missing_apps.append(app_name)
    
    if not missing_apps:
        print("✓ All applications from the backup are already installed!")
        return []
    
    print(f"Found {len(missing_apps)} missing application(s) that have data in the backup:")
    print()
    
    for i, app in enumerate(missing_apps, 1):
        install_info = get_installation_method(app)
        status = "Can auto-install" if install_info and install_info['method'] == 'cask' else "Manual install needed"
        print(f"  {i}. {app} - {status}")
    
    print()
    print("Would you like to install the missing applications?")
    print("  1. Install all automatically (where possible)")
    print("  2. Choose which ones to install")
    print("  3. Skip installation (you can install manually later)")
    print()
    
    while True:
        choice = input("Enter your choice (1-3): ").strip()
        if choice in ['1', '2', '3']:
            break
        print("Invalid choice. Please enter 1, 2, or 3.")
    
    if choice == '3':
        print("\nSkipping installation. You can install these apps manually later.")
        print("The restore will continue, but data for missing apps will be skipped.")
        return []
    
    apps_to_install = []
    
    if choice == '1':
        apps_to_install = missing_apps
    elif choice == '2':
        print("\nSelect applications to install (comma-separated numbers, e.g., 1,3,5):")
        selection = input("Your selection: ").strip()
        try:
            indices = [int(x.strip()) for x in selection.split(',')]
            apps_to_install = [missing_apps[i-1] for i in indices if 1 <= i <= len(missing_apps)]
        except:
            print("Invalid selection. Skipping installation.")
            return []
    
    # Install selected apps
    installed_apps = []
    print()
    print("=" * 60)
    print("INSTALLING APPLICATIONS")
    print("=" * 60)
    
    for app_name in apps_to_install:
        print(f"\n▶ Installing {app_name}...")
        install_info = get_installation_method(app_name)
        
        if install_info:
            if install_application(app_name, install_info):
                installed_apps.append(app_name)
        else:
            print(f"  ⚠ No automatic installation method available for {app_name}")
            print(f"  Please install manually from the App Store or vendor website")
    
    if installed_apps:
        print()
        print("=" * 60)
        print(f"Successfully installed {len(installed_apps)} application(s):")
        for app in installed_apps:
            print(f"  ✓ {app}")
        print("=" * 60)
    
    return installed_apps

def restore_chrome_profile(backup_dir, profile_name='Default'):
    """Restore Chrome profile from backup"""
    chrome_backup = os.path.join(backup_dir, 'Google_Chrome')
    
    if not os.path.exists(chrome_backup):
        print("  ✗ No Chrome backup found")
        return False
    
    chrome_path = os.path.expanduser("~/Library/Application Support/Google/Chrome")
    
    # Check if Chrome is installed
    if not os.path.exists(chrome_path):
        print("  ⚠ Chrome is not currently installed!")
        response = input("    Chrome must be installed to restore. Skip Chrome restore? (y/n): ").strip().lower()
        if response == 'y':
            return False
        else:
            print("    Please install Chrome first, then run restore again.")
            return False
    
    profile_backup_path = os.path.join(chrome_backup, profile_name.replace(' ', '_'))
    if not os.path.exists(profile_backup_path):
        print(f"  ✗ Profile '{profile_name}' not found in backup")
        return False
    
    profile_path = os.path.join(chrome_path, profile_name)
    
    # Check if profile already exists
    if os.path.exists(profile_path):
        print(f"  ⚠ Profile '{profile_name}' already exists")
        response = input(f"    Overwrite existing profile? This will replace ALL current data (y/n): ").strip().lower()
        if response != 'y':
            print("    Skipping...")
            return False
        
        # Create backup of existing profile
        existing_backup = profile_path + f"_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        print(f"    Creating backup of existing profile at: {existing_backup}")
        shutil.copytree(profile_path, existing_backup)
        shutil.rmtree(profile_path)
    
    # Restore the profile
    print(f"  Restoring Chrome profile '{profile_name}'...")
    try:
        shutil.copytree(profile_backup_path, profile_path)
        print(f"    ✓ Restored Chrome profile successfully")
        return True
    except Exception as e:
        print(f"    ✗ Error restoring profile: {e}")
        return False

def restore_application_support(backup_dir, app_name):
    """Restore application support data"""
    app_backup_path = os.path.join(backup_dir, 'Application_Settings', 'Application_Support', app_name)
    
    if not os.path.exists(app_backup_path):
        return False
    
    app_support_path = os.path.expanduser(f"~/Library/Application Support/{app_name}")
    
    # Check if app is installed by looking for the app bundle
    app_installed = check_if_installed(app_name, 'Application')
    
    if not app_installed and not os.path.exists(app_support_path):
        print(f"  ⚠ {app_name} doesn't appear to be installed")
        response = input(f"    Restore {app_name} data anyway? (y/n): ").strip().lower()
        if response != 'y':
            return False
    
    # Check if data already exists
    if os.path.exists(app_support_path):
        print(f"  ⚠ {app_name} data already exists")
        response = input(f"    Overwrite existing {app_name} data? (y/n): ").strip().lower()
        if response != 'y':
            print("    Skipping...")
            return False
        
        # Backup existing data
        existing_backup = app_support_path + f"_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        print(f"    Creating backup of existing data at: {existing_backup}")
        shutil.copytree(app_support_path, existing_backup)
        shutil.rmtree(app_support_path)
    
    # Restore the data
    try:
        shutil.copytree(app_backup_path, app_support_path)
        print(f"  ✓ Restored {app_name} data successfully")
        return True
    except Exception as e:
        print(f"  ✗ Error restoring {app_name}: {e}")
        return False

def restore_from_backup():
    """Main restore function"""
    print("=" * 60)
    print("RESTORE FROM BACKUP")
    print("=" * 60)
    print()
    
    # Find available backups
    backups = find_backup_directories()
    
    if not backups:
        print("No backup directories found in the current location.")
        print("Please make sure you're running this script in the same directory")
        print("where your backup folders are located (folders starting with 'mac_backup_').")
        return
    
    # Display available backups
    print("Available backups:")
    for i, backup in enumerate(backups, 1):
        timestamp_str = backup['timestamp']
        if isinstance(timestamp_str, str) and 'T' in timestamp_str:
            # Parse ISO format
            try:
                dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                timestamp_str = dt.strftime('%Y-%m-%d %H:%M:%S')
            except:
                pass
        
        print(f"  {i}. {backup['directory']}")
        print(f"     Created: {timestamp_str}")
        summary = backup['summary']
        print(f"     Chrome profiles: {summary.get('chrome_profiles_backed_up', 0)}")
        print(f"     Apps with sessions: {len(summary.get('apps_with_session_data', []))}")
        print()
    
    # Select backup
    while True:
        try:
            choice = input(f"Select backup to restore (1-{len(backups)}) or 'q' to quit: ").strip()
            if choice.lower() == 'q':
                return
            choice_num = int(choice)
            if 1 <= choice_num <= len(backups):
                selected_backup = backups[choice_num - 1]
                break
            print(f"Please enter a number between 1 and {len(backups)}")
        except ValueError:
            print("Please enter a valid number")
    
    backup_dir = selected_backup['directory']
    print(f"\nSelected backup: {backup_dir}")
    
    # Check for missing software and offer installation
    installed_apps = analyze_backup_and_offer_installation(backup_dir)
    
    # Show what can be restored
    print()
    print("=" * 60)
    print("RESTORE OPTIONS")
    print("=" * 60)
    print()
    print("What would you like to restore?")
    print("  1. Everything (all profiles and settings)")
    print("  2. Chrome profiles only")
    print("  3. Application settings and sessions only")
    print("  4. Custom selection")
    print()
    
    while True:
        restore_choice = input("Enter your choice (1-4): ").strip()
        if restore_choice in ['1', '2', '3', '4']:
            break
        print("Invalid choice. Please enter 1, 2, 3, or 4.")
    
    print()
    print("=" * 60)
    print("STARTING RESTORE")
    print("=" * 60)
    print()
    print("⚠ WARNING: Restoring will overwrite existing data!")
    print("   Make sure all applications are closed before continuing.")
    print()
    response = input("Continue with restore? (yes/no): ").strip().lower()
    
    if response != 'yes':
        print("Restore cancelled.")
        return
    
    print()
    restored_items = []
    
    # Restore based on choice
    if restore_choice == '1' or restore_choice == '2':
        # Restore Chrome
        print("Restoring Chrome profiles...")
        chrome_backup = os.path.join(backup_dir, 'Google_Chrome')
        if os.path.exists(chrome_backup):
            # Find all profiles in backup
            for item in os.listdir(chrome_backup):
                if item in ['Default', 'Profile_1', 'Profile_2', 'Profile_3', 'Profile_4', 'Profile_5']:
                    if restore_chrome_profile(backup_dir, item.replace('_', ' ')):
                        restored_items.append(f"Chrome {item}")
            
            # Restore Local State
            local_state_backup = os.path.join(chrome_backup, 'Local_State.json')
            if os.path.exists(local_state_backup):
                chrome_path = os.path.expanduser("~/Library/Application Support/Google/Chrome")
                if os.path.exists(chrome_path):
                    try:
                        shutil.copy2(local_state_backup, os.path.join(chrome_path, 'Local State'))
                        print("  ✓ Restored Chrome Local State")
                    except Exception as e:
                        print(f"  ✗ Error restoring Local State: {e}")
    
    if restore_choice == '1' or restore_choice == '3':
        # Restore Application Support data
        print("\nRestoring Application Support data...")
        app_support_backup = os.path.join(backup_dir, 'Application_Settings', 'Application_Support')
        
        if os.path.exists(app_support_backup):
            apps_to_restore = os.listdir(app_support_backup)
            print(f"  Found {len(apps_to_restore)} applications with backed up data")
            print()
            
            for app_name in apps_to_restore:
                print(f"  Restoring {app_name}...")
                if restore_application_support(backup_dir, app_name):
                    restored_items.append(app_name)
        
        # Restore preferences
        print("\nRestoring Preferences...")
        prefs_backup = os.path.join(backup_dir, 'Application_Settings', 'Preferences')
        if os.path.exists(prefs_backup):
            prefs_dir = os.path.expanduser("~/Library/Preferences")
            pref_count = 0
            for pref_file in os.listdir(prefs_backup):
                try:
                    src = os.path.join(prefs_backup, pref_file)
                    dest = os.path.join(prefs_dir, pref_file)
                    shutil.copy2(src, dest)
                    pref_count += 1
                except Exception as e:
                    pass
            print(f"  ✓ Restored {pref_count} preference files")
            restored_items.append(f"{pref_count} preference files")
        
        # Restore SSH
        print("\nRestoring SSH configuration...")
        ssh_backup = os.path.join(backup_dir, 'Application_Settings', 'SSH')
        if os.path.exists(ssh_backup):
            ssh_dir = os.path.expanduser("~/.ssh")
            if os.path.exists(ssh_dir):
                response = input("  ⚠ SSH config already exists. Overwrite? (y/n): ").strip().lower()
                if response != 'y':
                    print("    Skipping SSH restore...")
                else:
                    backup_existing = ssh_dir + f"_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    shutil.copytree(ssh_dir, backup_existing)
                    shutil.rmtree(ssh_dir)
                    shutil.copytree(ssh_backup, ssh_dir)
                    # Fix permissions
                    os.chmod(ssh_dir, 0o700)
                    for root, dirs, files in os.walk(ssh_dir):
                        for d in dirs:
                            os.chmod(os.path.join(root, d), 0o700)
                        for f in files:
                            if f.startswith('id_') and not f.endswith('.pub'):
                                os.chmod(os.path.join(root, f), 0o600)
                    print("  ✓ Restored SSH configuration")
                    restored_items.append("SSH config")
            else:
                shutil.copytree(ssh_backup, ssh_dir)
                os.chmod(ssh_dir, 0o700)
                print("  ✓ Restored SSH configuration")
                restored_items.append("SSH config")
    
    if restore_choice == '4':
        print("Custom selection not yet implemented. Using full restore...")
        print("(You can manually copy specific folders from the backup directory)")
    
    # Summary
    print()
    print("=" * 60)
    print("RESTORE COMPLETE")
    print("=" * 60)
    print()
    
    if installed_apps:
        print(f"Installed {len(installed_apps)} application(s):")
        for app in installed_apps:
            print(f"  ✓ {app}")
        print()
    
    print(f"Successfully restored {len(restored_items)} items:")
    for item in restored_items:
        print(f"  ✓ {item}")
    print()
    print("⚠ IMPORTANT: Please restart any applications you restored data for")
    print("   to ensure the restored settings take effect.")
    print()

def generate_report(all_software, format='txt'):
    """Generate report in specified format"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if format == 'txt':
        filename = f"mac_software_report_{timestamp}.txt"
        with open(filename, 'w') as f:
            f.write("=" * 80 + "\n")
            f.write("macOS Installed Software Report\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 80 + "\n\n")
            
            # Group by type
            by_type = {}
            for item in all_software:
                type_name = item['type']
                if type_name not in by_type:
                    by_type[type_name] = []
                by_type[type_name].append(item)
            
            for type_name in sorted(by_type.keys()):
                f.write(f"\n{type_name} ({len(by_type[type_name])} items)\n")
                f.write("-" * 80 + "\n")
                for item in sorted(by_type[type_name], key=lambda x: x['name'].lower()):
                    f.write(f"  {item['name']}\n")
                    f.write(f"    Version: {item['version']}\n")
                    if item['path'] != type_name and item['path'] != 'Unknown':
                        f.write(f"    Path: {item['path']}\n")
                    f.write("\n")
            
            f.write("\n" + "=" * 80 + "\n")
            f.write(f"Total software items: {len(all_software)}\n")
    
    elif format == 'csv':
        filename = f"mac_software_report_{timestamp}.csv"
        with open(filename, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['name', 'version', 'type', 'path'])
            writer.writeheader()
            writer.writerows(sorted(all_software, key=lambda x: (x['type'], x['name'].lower())))
    
    elif format == 'json':
        filename = f"mac_software_report_{timestamp}.json"
        with open(filename, 'w') as f:
            json.dump({
                'generated': datetime.now().isoformat(),
                'total_items': len(all_software),
                'software': sorted(all_software, key=lambda x: (x['type'], x['name'].lower()))
            }, f, indent=2)
    
    return filename

def main():
    print("=" * 60)
    print("macOS Software Scanner & Profile Backup/Restore Tool")
    print("=" * 60)
    print()
    print("What would you like to do?")
    print("  1. Backup - Create a backup of software list and profiles")
    print("  2. Restore - Restore from a previous backup")
    print("  3. Both - Create backup AND restore from existing backup")
    print()
    
    while True:
        choice = input("Enter your choice (1, 2, or 3): ").strip()
        if choice in ['1', '2', '3']:
            break
        print("Invalid choice. Please enter 1, 2, or 3.")
    
    print()
    
    if choice == '2' or choice == '3':
        # Restore mode
        restore_from_backup()
        if choice == '2':
            return
        print("\n" + "=" * 60)
        print("Now proceeding with backup...")
        print("=" * 60)
    
    # Backup mode (original functionality)
    print("Scanning your Mac for installed software...")
    print()
    
    all_software = []
    
    # Scan applications
    print("Scanning Applications folders...")
    apps = get_applications()
    all_software.extend(apps)
    print(f"  Found {len(apps)} applications")
    
    # Scan using system_profiler (more comprehensive)
    print("Scanning with system_profiler...")
    sys_apps = get_system_profile_apps()
    all_software.extend(sys_apps)
    print(f"  Found {len(sys_apps)} applications")
    
    # Scan Homebrew
    print("Scanning Homebrew packages...")
    brew_pkgs = get_homebrew_packages()
    all_software.extend(brew_pkgs)
    print(f"  Found {len(brew_pkgs)} Homebrew packages")
    
    # Scan Python packages
    print("Scanning Python packages...")
    python_pkgs = get_python_packages()
    all_software.extend(python_pkgs)
    print(f"  Found {len(python_pkgs)} Python packages")
    
    # Scan npm packages
    print("Scanning npm packages...")
    npm_pkgs = get_npm_packages()
    all_software.extend(npm_pkgs)
    print(f"  Found {len(npm_pkgs)} npm packages")
    
    print()
    print(f"Total software items found: {len(all_software)}")
    print()
    
    # Generate software reports
    print("Generating software reports...")
    txt_file = generate_report(all_software, 'txt')
    csv_file = generate_report(all_software, 'csv')
    json_file = generate_report(all_software, 'json')
    
    print(f"\nSoftware reports generated:")
    print(f"  Text:  {txt_file}")
    print(f"  CSV:   {csv_file}")
    print(f"  JSON:  {json_file}")
    
    # Create backup directory
    print("\n" + "=" * 60)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = f"mac_backup_{timestamp}"
    os.makedirs(backup_dir, exist_ok=True)
    print(f"Creating backups in: {backup_dir}")
    print("=" * 60)
    
    # Backup Chrome profiles
    chrome_backup_info = backup_chrome_profiles(backup_dir)
    
    # Backup other browser profiles
    other_browsers = backup_other_browser_profiles(backup_dir)
    
    # Backup application settings
    settings_backup = backup_application_settings(backup_dir)
    
    # Create summary report
    print("\n" + "=" * 60)
    print("BACKUP SUMMARY")
    print("=" * 60)
    
    summary = {
        'timestamp': datetime.now().isoformat(),
        'backup_directory': backup_dir,
        'chrome_profiles_backed_up': len(chrome_backup_info.get('profiles', [])),
        'other_browsers_backed_up': other_browsers,
        'preference_files_backed_up': settings_backup['preference_files'],
        'apps_with_session_data': settings_backup['apps_with_sessions'],
        'software_reports': {
            'text': txt_file,
            'csv': csv_file,
            'json': json_file
        }
    }
    
    summary_file = os.path.join(backup_dir, 'backup_summary.json')
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\nChrome profiles backed up: {summary['chrome_profiles_backed_up']}")
    print(f"Other browsers backed up: {', '.join(other_browsers) if other_browsers else 'None found'}")
    print(f"Preference files backed up: {settings_backup['preference_files']}")
    
    if settings_backup['apps_with_sessions']:
        print(f"\nApplications with session data backed up:")
        for app in settings_backup['apps_with_sessions']:
            print(f"  • {app['app']} - {app['description']}")
    
    print(f"\nBackup summary saved to: {summary_file}")
    print(f"\nAll backups saved in: {backup_dir}/")
    print("\n✓ Backup complete!")

if __name__ == "__main__":
    main()
