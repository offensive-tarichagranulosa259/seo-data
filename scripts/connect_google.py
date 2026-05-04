#!/usr/bin/env python3
"""Connect a Google account (covers both GSC and GA4).

Runs the OAuth loopback flow against the user's own Desktop-app OAuth
client. After consent, lists the GSC sites and GA4 properties the
account has access to, auto-selecting when there's only one of each.

Output is JSON on stdout so Claude can parse it. If the user has multiple
sites/properties, they'll need to call set_property.py to choose.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lib import config as cfg
from lib import google_auth


def main() -> int:
    parser = argparse.ArgumentParser(description="Connect Google account for GSC + GA4")
    parser.add_argument(
        "--client-secrets",
        help=f"Path to OAuth client JSON (default: {cfg.GOOGLE_CLIENT_FILE})",
    )
    args = parser.parse_args()

    try:
        tokens = google_auth.run_oauth_flow(args.client_secrets)
    except google_auth.MissingClientSecretsError as e:
        print(json.dumps({"ok": False, "error": str(e)}, indent=2), file=sys.stderr)
        return 2
    except Exception as e:
        print(json.dumps({"ok": False, "error": f"OAuth flow failed: {e}"}, indent=2), file=sys.stderr)
        return 1

    cfg.update("google", tokens=tokens)

    result: dict = {"ok": True, "google_connected": True}

    try:
        sites = google_auth.list_gsc_sites()
    except Exception as e:
        sites = []
        result["gsc_list_error"] = str(e)
    result["gsc_sites"] = sites

    try:
        properties = google_auth.list_ga4_properties()
    except Exception as e:
        properties = []
        result["ga4_list_error"] = str(e)
    result["ga4_properties"] = properties

    auto_selected: dict = {}

    if len(sites) == 1:
        site_url = sites[0]["siteUrl"]
        cfg.update("google", gsc_site=site_url)
        auto_selected["gsc_site"] = site_url
    elif sites:
        result["gsc_action_required"] = (
            "Multiple GSC sites available. Run: "
            "python scripts/set_property.py --provider gsc --site <siteUrl>"
        )
    else:
        result["gsc_warning"] = "No GSC sites found for this account."

    if len(properties) == 1:
        prop_id = properties[0]["property_id"]
        cfg.update("google", ga4_property=prop_id)
        auto_selected["ga4_property"] = prop_id
    elif properties:
        result["ga4_action_required"] = (
            "Multiple GA4 properties available. Run: "
            "python scripts/set_property.py --provider ga4 --property <id>"
        )
    else:
        result["ga4_warning"] = "No GA4 properties found for this account."

    if auto_selected:
        result["auto_selected"] = auto_selected

    print(json.dumps(result, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
