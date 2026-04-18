#!/usr/bin/env python3
#
###################################################################
# Project: software_scanner
# File: software_scanner/reports/__init__.py
# Purpose: Package initialization
#
# Description of code and how it works:
# Exports package components
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
from .generator import generate_report

__all__ = ["generate_report"]
