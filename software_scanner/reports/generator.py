#!/usr/bin/env python3
#
###################################################################
# Project: software_scanner
# File: software_scanner/reports/generator.py
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
import csv
import json
from datetime import datetime


def generate_report(all_software, fmt='txt'):
    """Generate a software report in the requested format (txt, csv, or json)"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    handlers = {'txt': _write_txt, 'csv': _write_csv, 'json': _write_json}
    if fmt not in handlers:
        raise ValueError(f"Unsupported format: {fmt!r}. Choose from {list(handlers)}")
    filename = f"mac_software_report_{timestamp}.{fmt}"
    handlers[fmt](filename, all_software)
    return filename


def _write_txt(filename, software):
    by_type = {}
    for item in software:
        by_type.setdefault(item['type'], []).append(item)

    with open(filename, 'w') as f:
        f.write("=" * 80 + "\n")
        f.write("macOS Installed Software Report\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 80 + "\n")

        for type_name in sorted(by_type):
            items = by_type[type_name]
            f.write(f"\n{type_name} ({len(items)} items)\n")
            f.write("-" * 80 + "\n")
            for item in sorted(items, key=lambda x: x['name'].lower()):
                f.write(f"  {item['name']}\n")
                f.write(f"    Version: {item['version']}\n")
                if item['path'] not in (type_name, 'Unknown'):
                    f.write(f"    Path: {item['path']}\n")
                f.write("\n")

        f.write("\n" + "=" * 80 + "\n")
        f.write(f"Total software items: {len(software)}\n")


def _write_csv(filename, software):
    with open(filename, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['name', 'version', 'type', 'path'])
        writer.writeheader()
        writer.writerows(sorted(software, key=lambda x: (x['type'], x['name'].lower())))


def _write_json(filename, software):
    with open(filename, 'w') as f:
        json.dump(
            {
                'generated': datetime.now().isoformat(),
                'total_items': len(software),
                'software': sorted(software, key=lambda x: (x['type'], x['name'].lower())),
            },
            f,
            indent=2,
        )
