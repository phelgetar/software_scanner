#!/usr/bin/env python3
"""
Add complete standardized headers to Python and Shell files
"""
import argparse
import glob as globlib
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Tuple

# Header template for Python files
PYTHON_HEADER_TEMPLATE = '''#!/usr/bin/env python3
#
###################################################################
# Project: {project}
# File: {filepath}
# Purpose: {purpose}
#
# Description of code and how it works:
# {description}
#
# Author: {author}
# Created: {created}
#
# Version: {version}
# Last Modified: {modified} by {author}
#
# Revision History:
# - {version} ({modified}): {revision_note}
###################################################################
#
'''

# Header template for Shell files
SHELL_HEADER_TEMPLATE = '''#!/usr/bin/env bash
#
###################################################################
# Project: {project}
# File: {filepath}
# Purpose: {purpose}
#
# Description of code and how it works:
# {description}
#
# Author: {author}
# Created: {created}
#
# Version: {version}
# Last Modified: {modified} by {author}
#
# Revision History:
# - {version} ({modified}): {revision_note}
###################################################################
#
'''

def has_header(content: str) -> bool:
    """Check if file already has a standardized header"""
    return '###################################################################' in content[:500]

def iter_target_files(paths: List[str], globs: List[str]) -> List[Path]:
    """
    Iterate through target files based on paths and glob patterns
    
    Args:
        paths: List of files or directories to search
        globs: List of glob patterns (e.g., ['*.py', '**/*.sh'])
    
    Returns:
        List of Path objects matching the criteria
    """
    seen = set()
    results = []
    allowed_exts = {'.py', '.sh'}
    
    for path_str in paths:
        path = Path(path_str)
        
        if path.is_file():
            # Direct file path
            if path.suffix in allowed_exts and path not in seen:
                seen.add(path)
                results.append(path)
        
        elif path.is_dir():
            # Directory - apply globs (default is recursive)
            patterns = globs if globs else ['**/*.py', '**/*.sh']

            for pattern in patterns:
                matches = path.glob(pattern)
                
                for file_path in matches:
                    if file_path.is_file() and file_path.suffix in allowed_exts:
                        if file_path not in seen:
                            seen.add(file_path)
                            results.append(file_path)
        else:
            print(f"⚠️  Path not found: {path}")
    
    return sorted(results)

def get_default_description(filepath: Path, base_purpose: str = None) -> Tuple[str, str]:
    """
    Get purpose and description for a file
    
    Args:
        filepath: Path to the file
        base_purpose: Optional base purpose to use
    
    Returns:
        Tuple of (purpose, description)
    """
    filename = filepath.name
    
    # Check for common patterns
    if 'client' in filename.lower():
        purpose = base_purpose or "API client"
        description = "Handles API requests and responses"
    elif 'transformer' in filename.lower() or 'transform' in filename.lower():
        purpose = base_purpose or "Data transformer"
        description = "Transforms external data into standardized format"
    elif 'router' in filename.lower():
        purpose = base_purpose or "Request router"
        description = "HTTP endpoints and request handlers"
    elif 'test' in filename.lower():
        purpose = base_purpose or "Test script"
        description = "Validates functionality and connectivity"
    elif filename == '__init__.py':
        purpose = base_purpose or "Package initialization"
        description = "Exports package components"
    elif 'backup' in filename.lower():
        purpose = base_purpose or "Backup utility"
        description = "Creates and manages backups"
    elif 'restore' in filename.lower():
        purpose = base_purpose or "Restore utility"
        description = "Restores from backups"
    elif 'validate' in filename.lower():
        purpose = base_purpose or "Validation utility"
        description = "Validates data and configuration"
    else:
        purpose = base_purpose or "Utility script"
        description = "Helper functionality"
    
    return purpose, description

def add_header_to_file(
    filepath: Path,
    project: str,
    author: str,
    version: str,
    created: str,
    purpose: str = None,
    description: str = None,
    revision_note: str = None,
    force: bool = False,
    dry_run: bool = False
) -> bool:
    """
    Add standardized header to a Python or Shell file
    
    Args:
        filepath: Path to file
        project: Project name
        author: Author name
        version: Version number
        created: Creation date
        purpose: Optional custom purpose
        description: Optional custom description
        revision_note: Optional custom revision note
        force: Force overwrite existing headers
        dry_run: Preview without writing
    
    Returns:
        True if file was modified, False otherwise
    """
    # Read existing content
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    # Check if already has header
    if has_header(content) and not force:
        print(f"⚠️  {filepath.name} already has a header - skipping (use --force to overwrite)")
        return False
    
    # Determine file type
    is_python = filepath.suffix == '.py'
    is_shell = filepath.suffix == '.sh'
    
    if not (is_python or is_shell):
        print(f"⚠️  {filepath.name} - unsupported file type")
        return False
    
    # Get template
    template = PYTHON_HEADER_TEMPLATE if is_python else SHELL_HEADER_TEMPLATE
    
    # Remove existing shebang if present
    if is_python and content.startswith('#!/usr/bin/env python3'):
        content = content.split('\n', 1)[1] if '\n' in content else ''
    elif is_shell and content.startswith('#!/usr/bin/env bash'):
        content = content.split('\n', 1)[1] if '\n' in content else ''
    
    # Remove existing header if forcing
    if force and has_header(content):
        lines = content.split('\n')
        # Find end of header block
        end_idx = 0
        in_header = False
        for i, line in enumerate(lines):
            if '###################################################################' in line:
                if not in_header:
                    in_header = True
                else:
                    # Second occurrence - end of header
                    end_idx = i + 1
                    break
        if end_idx > 0:
            content = '\n'.join(lines[end_idx:])
    
    # Remove docstring if it's the first thing (Python only)
    if is_python and (content.lstrip().startswith('"""') or content.lstrip().startswith("'''")):
        lines = content.lstrip().split('\n')
        quote = '"""' if content.lstrip().startswith('"""') else "'''"
        end_idx = 1
        for i, line in enumerate(lines[1:], 1):
            if quote in line:
                end_idx = i + 1
                break
        content = '\n'.join(lines[end_idx:])
    
    # Get description for this file
    default_purpose, default_description = get_default_description(filepath, purpose)
    final_purpose = purpose or default_purpose
    final_description = description or default_description
    final_revision = revision_note or "Initial version"
    
    # Prepare relative filepath
    try:
        rel_path = str(filepath.relative_to(Path.cwd()))
    except ValueError:
        rel_path = str(filepath)
    
    # Build header
    header = template.format(
        project=project,
        filepath=rel_path,
        purpose=final_purpose,
        description=final_description,
        author=author,
        created=created,
        version=version,
        modified=created,
        revision_note=final_revision
    )
    
    # Combine header with content
    new_content = header + content.lstrip()
    
    if dry_run:
        print(f"🔍 {filepath.name} - would add header")
        return True
    
    # Write back
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"✅ {filepath.name} - header added")
    return True

def main():
    parser = argparse.ArgumentParser(
        description='Add standardized headers to Python and Shell files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Add headers to all Python and shell files recursively
  python add_headers.py --paths software_scanner/

  # Add headers to specific files
  python add_headers.py --paths file1.py file2.sh

  # Use glob patterns
  python add_headers.py --paths software_scanner/ --glob "**/*.py"

  # Multiple directories and patterns
  python add_headers.py --paths software_scanner/ tests/ --glob "*.py" "*.sh"

  # Dry run to preview
  python add_headers.py --paths software_scanner/ --dry-run

  # Custom purpose and description
  python add_headers.py --paths myfile.py --purpose "Custom purpose" --description "Custom description"
        '''
    )
    
    parser.add_argument(
        '--paths',
        nargs='+',
        required=True,
        help='Files or directories to process'
    )
    parser.add_argument(
        '--glob',
        nargs='+',
        default=[],
        help='Glob patterns to match files (e.g., *.py, **/*.sh)'
    )
    parser.add_argument(
        '--project',
        default='software_scanner',
        help='Project name (default: software_scanner)'
    )
    parser.add_argument(
        '--author',
        default='Tim Canady',
        help='Author name (default: Tim Canady)'
    )
    parser.add_argument(
        '--version',
        default='1.0.0',
        help='Version number (default: 1.0.0)'
    )
    parser.add_argument(
        '--created',
        default=datetime.now().strftime("%Y-%m-%d"),
        help='Creation date (default: today)'
    )
    parser.add_argument(
        '--purpose',
        help='Custom purpose (overrides auto-detection)'
    )
    parser.add_argument(
        '--description',
        help='Custom description (overrides auto-detection)'
    )
    parser.add_argument(
        '--revision-note',
        default='Initial version',
        help='Revision history note (default: Initial version)'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Overwrite existing headers'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview changes without writing'
    )
    parser.add_argument(
        '--yes',
        action='store_true',
        help='Skip confirmation prompt'
    )
    
    args = parser.parse_args()
    
    # Find target files
    files = iter_target_files(args.paths, args.glob)
    
    if not files:
        print("❌ No matching files found")
        print(f"   Paths: {args.paths}")
        print(f"   Globs: {args.glob or ['*.py', '*.sh']}")
        sys.exit(1)
    
    print(f"📁 Found {len(files)} file(s):")
    for f in files:
        print(f"   - {f}")
    print()
    
    # Ask for confirmation unless --yes
    if not args.yes and not args.dry_run:
        response = input("Add headers to these files? [y/N]: ").strip().lower()
        if response != 'y':
            print("Aborted.")
            sys.exit(0)
        print()
    
    # Process each file
    updated = 0
    for filepath in files:
        if add_header_to_file(
            filepath=filepath,
            project=args.project,
            author=args.author,
            version=args.version,
            created=args.created,
            purpose=args.purpose,
            description=args.description,
            revision_note=args.revision_note,
            force=args.force,
            dry_run=args.dry_run
        ):
            updated += 1
    
    print()
    if args.dry_run:
        print(f"🔍 Dry run complete - {updated}/{len(files)} file(s) would be updated")
    else:
        print(f"✅ Done! Updated {updated}/{len(files)} file(s)")
        
        if updated > 0:
            print()
            print("Next steps:")
            print("  1. Review the files to ensure headers look correct")
            print("  2. Customize any 'Description' sections if needed")
            print("  3. Commit changes to git")

if __name__ == "__main__":
    main()
