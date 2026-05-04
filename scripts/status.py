#!/usr/bin/env python3
"""Print connection status as JSON.

Used by the skill (and by humans) to see what providers are connected and
which property is selected for each. Never prints tokens or API keys.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lib import config as cfg


def main() -> int:
    config = cfg.load_config()
    google = config.get("google", {})
    bing = config.get("bing", {})

    google_connected = bool(google.get("tokens"))
    bing_connected = bool(bing.get("api_key"))

    status = {
        "config_dir": str(cfg.CONFIG_DIR),
        "google": {
            "connected": google_connected,
            "client_secrets_present": cfg.GOOGLE_CLIENT_FILE.exists(),
        },
        "gsc": {
            "ready": google_connected and bool(google.get("gsc_site")),
            "site": google.get("gsc_site"),
        },
        "ga4": {
            "ready": google_connected and bool(google.get("ga4_property")),
            "property": google.get("ga4_property"),
        },
        "bing": {
            "connected": bing_connected,
            "ready": bing_connected and bool(bing.get("site")),
            "site": bing.get("site"),
        },
    }

    print(json.dumps(status, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
