"""Bing Webmaster Tools API key handling.

Unlike Google, Bing's API uses a static API key (no OAuth). User generates
it from bing.com/webmasters → Settings → API Access. We validate the key by
calling GetUserSites and store it in config.json.
"""

from __future__ import annotations

from typing import Any

from . import config as cfg


BING_API_BASE = "https://ssl.bing.com/webmaster/api.svc/json"


class NotConnectedError(RuntimeError):
    pass


class InvalidApiKeyError(RuntimeError):
    pass


def get_api_key() -> str:
    config = cfg.load_config()
    key = config.get("bing", {}).get("api_key")
    if not key:
        raise NotConnectedError(
            "Bing is not connected. Run: python scripts/connect_bing.py --api-key <KEY>"
        )
    return key


def get_site() -> str:
    config = cfg.load_config()
    site = config.get("bing", {}).get("site")
    if not site:
        raise NotConnectedError(
            "No Bing site selected. Run: python scripts/set_property.py --provider bing"
        )
    return site


def list_sites(api_key: str) -> list[dict[str, Any]]:
    """Call GetUserSites to validate the key and return verified sites."""
    import requests

    url = f"{BING_API_BASE}/GetUserSites"
    try:
        resp = requests.get(url, params={"apikey": api_key}, timeout=20)
    except requests.RequestException as e:
        raise InvalidApiKeyError(f"Network error reaching Bing API: {e}") from e

    if resp.status_code == 401 or resp.status_code == 403:
        raise InvalidApiKeyError(
            "Bing rejected the API key (401/403). Check that the key is correct and active "
            "at bing.com/webmasters → Settings → API Access."
        )
    if not resp.ok:
        raise InvalidApiKeyError(
            f"Bing API returned HTTP {resp.status_code}: {resp.text[:200]}"
        )

    try:
        data = resp.json()
    except ValueError as e:
        raise InvalidApiKeyError(f"Could not parse Bing response as JSON: {e}") from e

    sites = data.get("d", []) or []
    return [
        {
            "url": s.get("Url"),
            "verified": s.get("IsVerified", False),
        }
        for s in sites
    ]


def call(method: str, params: dict[str, Any] | None = None) -> Any:
    """Call a Bing Webmaster API method using the stored key + site."""
    import requests

    api_key = get_api_key()
    site_url = get_site()

    full_params = {"apikey": api_key, "siteUrl": site_url}
    if params:
        full_params.update(params)

    url = f"{BING_API_BASE}/{method}"
    resp = requests.get(url, params=full_params, timeout=30)
    if not resp.ok:
        raise RuntimeError(f"Bing API {method} failed HTTP {resp.status_code}: {resp.text[:300]}")
    data = resp.json()
    return data.get("d")
