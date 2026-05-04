#!/usr/bin/env python3
"""Pick or change which GSC site / GA4 property / Bing site to use.

Usage patterns:

    # List available options for a provider
    python scripts/set_property.py --provider gsc
    python scripts/set_property.py --provider ga4
    python scripts/set_property.py --provider bing

    # Select a property
    python scripts/set_property.py --provider gsc --site https://example.com/
    python scripts/set_property.py --provider ga4 --property 123456789
    python scripts/set_property.py --provider bing --site https://example.com/
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lib import config as cfg


def list_gsc() -> dict:
    from lib import google_auth
    sites = google_auth.list_gsc_sites()
    return {"sites": sites, "count": len(sites)}


def list_ga4() -> dict:
    from lib import google_auth
    properties = google_auth.list_ga4_properties()
    return {"properties": properties, "count": len(properties)}


def list_bing() -> dict:
    from lib import bing_auth
    api_key = bing_auth.get_api_key()
    sites = bing_auth.list_sites(api_key)
    return {"sites": sites, "count": len(sites)}


def main() -> int:
    parser = argparse.ArgumentParser(description="Set the active property for a provider")
    parser.add_argument("--provider", required=True, choices=["gsc", "ga4", "bing"])
    parser.add_argument("--site", help="Site URL (for gsc/bing)")
    parser.add_argument("--property", dest="property_id", help="GA4 property ID (numeric)")
    args = parser.parse_args()

    try:
        if args.provider == "gsc":
            if args.site:
                cfg.update("google", gsc_site=args.site)
                print(json.dumps({"ok": True, "gsc_site": args.site}, indent=2))
            else:
                print(json.dumps({"ok": True, **list_gsc()}, indent=2, default=str))

        elif args.provider == "ga4":
            if args.property_id:
                cfg.update("google", ga4_property=args.property_id)
                print(json.dumps({"ok": True, "ga4_property": args.property_id}, indent=2))
            else:
                print(json.dumps({"ok": True, **list_ga4()}, indent=2, default=str))

        elif args.provider == "bing":
            if args.site:
                cfg.update("bing", site=args.site)
                print(json.dumps({"ok": True, "bing_site": args.site}, indent=2))
            else:
                print(json.dumps({"ok": True, **list_bing()}, indent=2, default=str))

    except Exception as e:
        print(json.dumps({"ok": False, "error": str(e)}, indent=2), file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
