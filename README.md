# macOS Software Scanner & Profile Backup Tool

A Python package that scans your Mac for installed software and creates complete backups of browser profiles, application settings, and configurations. Supports full restore from backup, including automatic installation of missing applications via Homebrew.

## Project Structure

```
software_scanner/
├── main.py                          # Entry point (runs software_scanner.cli:main)
├── mac_software_scanner.py          # Original monolithic script (reference)
├── pyproject.toml                   # Package config; installs `software-scanner` CLI
├── validate_headers.py              # Root-level header validator (pre-commit)
├── software_scanner/                # Main package
│   ├── __init__.py                  # Package version (3.0.0)
│   ├── cli.py                       # Interactive menu and backup orchestrator
│   ├── scanner/                     # Software discovery
│   │   ├── applications.py          # .app bundles from /Applications
│   │   ├── homebrew.py              # Homebrew formulae and casks
│   │   ├── python_packages.py       # pip3 package list
│   │   └── npm_packages.py          # npm global packages
│   ├── backup/                      # Backup operations
│   │   ├── chrome.py                # Chrome/Chromium-based profiles
│   │   ├── browsers.py              # Firefox, Safari, Brave, Edge, Opera
│   │   └── app_settings.py          # Preferences, app support, SSH, VS Code, etc.
│   ├── restore/                     # Restore operations
│   │   ├── manager.py               # Interactive restore orchestrator
│   │   └── installer.py             # Homebrew-based auto-installation (35+ apps)
│   ├── reports/                     # Report generation
│   │   └── generator.py             # TXT, CSV, JSON report output
│   ├── utils/                       # Shared utilities
│   │   ├── shell.py                 # run_command() subprocess wrapper
│   │   └── fs.py                    # format_size() helper
│   └── scripts/                     # Repo management tools
│       ├── versions.yml             # Semver registry for all tracked files
│       ├── validate_headers.py      # Dual-mode header validator
│       ├── add_headers.py           # Insert standard headers into files
│       ├── dry-run.sh               # Pre-commit smoke check
│       ├── validation.sh            # Install git pre-commit hook
│       ├── bump_version.py          # Bump project_version in versions.yml
│       ├── bump_file_versions.py    # Bump individual file versions + CHANGELOG
│       ├── init_versions.py         # Seed versions.yml from file scan
│       ├── cleanup.py               # Repo housekeeping utilities
│       ├── safe_header_apply.py     # Dry-run wrapper for add_headers.py
│       ├── edit_header_section.py   # In-place header field editor
│       ├── apply_headers.py         # Low-level header write utility
│       ├── git_bootstrap.sh         # One-time git hook setup
│       ├── release_tag.sh           # Tag a release in git
│       ├── backup_files.sh          # Filesystem backup with rotation
│       ├── backup_mysql.sh          # MySQL dump with rotation
│       ├── backup_snapshots.sh      # Snapshot copy from daily backups
│       ├── restore_files.sh         # Restore from tar.gz archive
│       └── restore_mysql.sh         # Restore MySQL from gzip dump
└── tests/
    ├── test_scanner.py
    ├── test_reports.py
    └── test_restore.py
```

## Features

### Software Scanning
- **Applications** — scans `/Applications` and `~/Applications` for `.app` bundles; reads version from `Info.plist`
- **system_profiler** — uses `SPApplicationsDataType` for comprehensive discovery
- **Homebrew** — all formulae and casks with versions
- **Python packages** — `pip3 list` output
- **npm packages** — globally installed npm packages

### Browser Profile Backups

#### Chrome and Chrome-based Browsers
Backs up per-profile: Bookmarks, Cookies, History, Login Data, Preferences, Extensions, Web Data, Favicons, Top Sites, Storage, Sessions folder, Current Session/Tabs (open tabs).

Supports: Google Chrome, Google Chrome Canary, Chromium, Brave, Microsoft Edge, Opera.

#### Firefox
Complete profile directory backup.

#### Safari
Bookmarks.plist, History.db, Cookies.binarycookies, Downloads history, Last Session, Top Sites.

### Application Settings Backups
- **macOS Preferences** — all `.plist` files from `~/Library/Preferences`
- **Application Support** — session data for 35+ apps including:
  BBEdit, Sublime Text, Atom, TextMate, MacVim, iTerm2, Terminal, Postman, Obsidian, Notion, JetBrains IDEs, TablePlus, Sequel Pro/Ace, Notes, Bear, and more
- **Saved Application State** — window positions, unsaved app data
- **App Containers** — sandboxed app data (TextEdit, Pages, Numbers, Keynote, etc.)
- **SSH** — keys and config (permissions set to 600 on restore)
- **Git** — `.gitconfig`
- **Shell profiles** — `.bashrc`, `.bash_profile`, `.zshrc`, `.zprofile`, `.profile`
- **VS Code** — complete user settings

## Installation

### Requirements
- macOS (tested on macOS 10.14+)
- Python 3.9 or higher
- Optional: [Homebrew](https://brew.sh) for automatic app installation on restore

### Install as a package

```bash
pip install -e .
```

This installs the `software-scanner` CLI command.

### No additional dependencies required
The core tool uses only Python standard library modules. Repo management scripts (`bump_file_versions.py`, etc.) optionally use `pyyaml`.

## Usage

### Run via CLI (after `pip install -e .`)

```bash
software-scanner
```

### Run directly

```bash
python3 main.py
# or
python3 mac_software_scanner.py
```

### Choose your operation

```
  1. Backup  - Scan software and create a backup
  2. Restore - Restore from a previous backup
  3. Both    - Restore first, then create a new backup
```

### Backup Mode

When you select backup, the tool will:
1. Scan all installed software across all sources
2. Generate reports (TXT, CSV, JSON)
3. Back up all browser profiles
4. Back up application settings and sessions
5. Create a timestamped backup directory: `mac_backup_YYYYMMDD_HHMMSS/`

### Restore Mode

When you select restore, the tool will:
1. Find all `mac_backup_*/` directories in the current working directory
2. Display backup details and let you choose which to restore from
3. Analyze missing software and offer automatic installation via Homebrew
4. Present restore options: everything, Chrome only, app settings only, or custom
5. Check for conflicts, warn if apps aren't installed, back up existing data before overwriting

#### Automatic Software Installation (35+ apps)

During restore the tool detects which apps had data in the backup but aren't currently installed, then offers to install them automatically via `brew install --cask`.

Supported: Chrome, Firefox, Brave, Edge, Opera, BBEdit, Sublime Text, VS Code, Atom, TextMate, MacVim, all JetBrains IDEs, iTerm2, TablePlus, Sequel Pro, Sequel Ace, Postman, Docker, Slack, Discord, Zoom, Obsidian, Notion, Bear, and more.

## Output

### Software Reports (created in CWD)
- `mac_software_report_TIMESTAMP.txt`
- `mac_software_report_TIMESTAMP.csv`
- `mac_software_report_TIMESTAMP.json`

### Backup Directory Layout
```
mac_backup_TIMESTAMP/
├── Google_Chrome/
│   ├── Default/
│   │   ├── Bookmarks
│   │   ├── Cookies
│   │   ├── Preferences.json
│   │   ├── History
│   │   ├── Current_Session
│   │   ├── Current_Tabs
│   │   ├── Sessions/
│   │   └── Extensions/
│   └── Local_State.json
├── Firefox_Backup/
├── Safari_Backup/
├── Brave_Backup/
├── Application_Settings/
│   ├── Preferences/
│   ├── Application_Support/
│   │   ├── BBEdit/
│   │   ├── Sublime Text/
│   │   ├── iTerm2/
│   │   └── ...
│   ├── Saved_Application_State/
│   ├── Containers/
│   ├── SSH/
│   ├── VSCode/
│   ├── gitconfig
│   └── .zshrc
├── backup_manifest.json
└── backup_summary.json
```

## Repo Management Scripts

The `software_scanner/scripts/` directory contains utilities for maintaining the codebase itself.

### Header Management

All `.py` and `.sh` files carry a standardized header block with fields:
`Project`, `File`, `Purpose`, `Author`, `Created`, `Version`, `Last Modified`, `Revision History`.

```bash
# Add headers to all files (recursive)
python software_scanner/scripts/add_headers.py --paths software_scanner/ tests/

# Validate headers in staged files (pre-commit) or a directory (manual)
python software_scanner/scripts/validate_headers.py                       # staged files
python software_scanner/scripts/validate_headers.py software_scanner/     # directory

# Full dry-run check (versions.yml + headers)
bash software_scanner/scripts/dry-run.sh

# Install pre-commit git hook
bash software_scanner/scripts/validation.sh
```

### Version Management

```bash
# Seed versions.yml from a file scan
python software_scanner/scripts/init_versions.py

# Bump project version
python software_scanner/scripts/bump_version.py patch    # or minor / major

# Bump a specific file's version and append to CHANGELOG
python software_scanner/scripts/bump_file_versions.py software_scanner/cli.py "Fix menu logic" patch
python software_scanner/scripts/bump_file_versions.py "software_scanner/*" "Update all" minor
```

### Backup / Restore Utilities

```bash
# File system backup with daily rotation
bash software_scanner/scripts/backup_files.sh [source_dir]

# MySQL dump
bash software_scanner/scripts/backup_mysql.sh

# Snapshot from latest daily
bash software_scanner/scripts/backup_snapshots.sh

# Restore file archive
bash software_scanner/scripts/restore_files.sh /var/backups/software_scanner/snapshots/archive.tar.gz

# Restore MySQL
bash software_scanner/scripts/restore_mysql.sh
```

## Important Notes

### Security & Privacy
- **Passwords** — Login Data files are backed up but remain encrypted by macOS keychain
- **SSH keys** — private keys are included in the backup; keep it in a secure location
- **Cookies** — may contain authentication tokens
- Permissions for SSH private keys are automatically restored to `600`

### Browser Considerations
- Close browsers before running for the most reliable backup
- Chrome profiles with many extensions can be several GB
- If you use browser sync (Chrome Sync, Firefox Sync) your data is already in the cloud

### What Is NOT Backed Up
- Browser cache
- Downloaded files
- Application binaries (reinstall from the software list or Homebrew)
- User documents

## Common Use Cases

### Moving to a New Mac
1. Run backup on the old Mac
2. Transfer the `mac_backup_*/` folder (external drive, AirDrop, cloud)
3. Run the tool on the new Mac and select Restore
4. Script detects missing apps and installs them via Homebrew
5. All settings, profiles, and sessions are restored

### Regular Backups
Run periodically (weekly/monthly). Each backup is independent and timestamped. Restore from any backup point.

## Troubleshooting

### Permission denied errors
Some system files require elevated permissions. The script continues and backs up what it can access.

### "Application not installed" warning
The script will offer to install the missing app via Homebrew. Choose Install, or skip and install manually later.

### Chrome won't start after restore
Ensure Chrome was fully closed before restore. Try restarting your Mac.

### Tabs didn't restore
Chrome should prompt to restore session on startup. If not: History → Recently Closed. You can also inspect the Sessions folder in the backup directly.

### SSH keys not working
The script automatically sets permissions to `600`. If issues persist: `chmod 600 ~/.ssh/id_*`

## Changelog

### Version 3.0.0 (Current)
- Refactored from single-file script into a proper Python package (`software_scanner`)
- Installable via `pip install -e .` with `software-scanner` CLI entry point
- Subpackages: `scanner`, `backup`, `restore`, `reports`, `utils`
- `scripts/` directory with full repo management toolchain (headers, versioning, backups)
- Automatic app installation during restore (35+ apps via Homebrew Cask)
- Full restore functionality with interactive mode and conflict detection
- Safety backups created before any overwrite

### Version 2.0
- Chrome profile backup (bookmarks, cookies, preferences, open tabs)
- Multi-browser support: Chrome variants, Firefox, Safari
- Application settings backup (SSH, Git, shell profiles, VS Code)
- Backup manifest and summary files

### Version 1.0
- Initial release: software scanning only

## License

Free to use and modify for personal or commercial purposes.
