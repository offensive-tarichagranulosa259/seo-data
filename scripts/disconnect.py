#!/usr/bin/env python3
"""Disconnect a provider — clears its tokens/keys and selected property.

Usage:
    python scripts/disconnect.py google
    python scripts/disconnect.py bing
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lib import config as cfg


PROVIDERS = {"google", "bing"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Disconnect a provider")
    parser.add_argument("provider", choices=sorted(PROVIDERS), help="Which provider to disconnect")
    args = parser.parse_args()

    cfg.clear_section(args.provider)
    print(json.dumps({"ok": True, "disconnected": args.provider}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
