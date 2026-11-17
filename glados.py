#!/usr/bin/env python3
"""Compatibility entry point; keep check-in logic in one implementation."""
import sys
from checkin import (GLaDOS, format_traffic, load_accounts, main,
                     notify, notify_serverchan, notify_telegram)

if __name__ == "__main__":
    sys.exit(main())
