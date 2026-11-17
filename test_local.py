#!/usr/bin/env python3
"""Compatibility entry point; for the current website use browser_checkin.py."""
import sys
from checkin import main

if __name__ == "__main__":
    sys.exit(main())
