#!/usr/bin/env python3
"""Connect Bing Webmaster Tools using an API key.

User generates the key at bing.com/webmasters → Settings → API Access.
We validate by calling GetUserSites; on success we list verified sites
and auto-select if only one exists.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lib import config as cfg
from lib import bing_auth


def main() -> int:
    parser = argparse.ArgumentParser(description="Connect Bing Webmaster Tools")
    parser.add_argument("--api-key", required=True, help="Bing Webmaster API key")
    args = parser.parse_args()

    try:
        sites = bing_auth.list_sites(args.api_key)
    except bing_auth.InvalidApiKeyError as e:
        print(json.dumps({"ok": False, "error": str(e)}, indent=2), file=sys.stderr)
        return 2
    except Exception as e:
        print(json.dumps({"ok": False, "error": f"Bing connection failed: {e}"}, indent=2), file=sys.stderr)
        return 1

    cfg.update("bing", api_key=args.api_key)

    verified = [s for s in sites if s.get("verified")]
    result: dict = {
        "ok": True,
        "bing_connected": True,
        "sites": sites,
        "verified_count": len(verified),
    }

    if len(verified) == 1:
        site_url = verified[0]["url"]
        cfg.update("bing", site=site_url)
        result["auto_selected_site"] = site_url
    elif verified:
        result["action_required"] = (
            "Multiple verified Bing sites. Run: "
            "python scripts/set_property.py --provider bing --site <url>"
        )
    else:
        result["warning"] = "No verified sites on this Bing account."

    print(json.dumps(result, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
