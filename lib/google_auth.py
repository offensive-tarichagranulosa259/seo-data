"""Google OAuth flow + credential management for GSC and GA4.

Uses a Desktop-app OAuth client supplied by the user (since
webmasters.readonly and analytics.readonly are restricted scopes — we
cannot ship a shared client). The client config lives at
~/.seo-data/google_client.json (or path passed via CLI).

Tokens (refresh + access) are stored inside config.json under
config["google"]["tokens"] as a serialized dict.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from . import config as cfg


SCOPES = [
    "https://www.googleapis.com/auth/webmasters.readonly",
    "https://www.googleapis.com/auth/analytics.readonly",
]


class NotConnectedError(RuntimeError):
    pass


class MissingClientSecretsError(RuntimeError):
    pass


def _load_client_secrets(client_secrets_path: Optional[str] = None) -> dict:
    path = Path(client_secrets_path) if client_secrets_path else cfg.GOOGLE_CLIENT_FILE
    if not path.exists():
        raise MissingClientSecretsError(
            f"OAuth client config not found at {path}.\n"
            f"Create a Desktop-app OAuth client in Google Cloud Console and save the "
            f"downloaded JSON to {cfg.GOOGLE_CLIENT_FILE} (or pass --client-secrets <path>). "
            f"See README for the 5-minute walkthrough."
        )
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def run_oauth_flow(client_secrets_path: Optional[str] = None) -> dict:
    """Run the loopback OAuth flow. Opens the user's browser. Returns
    the credentials dict ready to be persisted."""
    from google_auth_oauthlib.flow import InstalledAppFlow

    client_config = _load_client_secrets(client_secrets_path)
    flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
    creds = flow.run_local_server(
        port=0,
        prompt="consent",
        access_type="offline",
        authorization_prompt_message="Opening your browser for Google consent...",
        success_message="Authentication complete. You can close this tab.",
        open_browser=True,
    )
    return _serialize_credentials(creds)


def get_credentials():
    """Load saved credentials, refreshing access token if needed.

    Returns a google.oauth2.credentials.Credentials object.
    Raises NotConnectedError if the user hasn't connected Google yet.
    """
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request

    config = cfg.load_config()
    tokens = config.get("google", {}).get("tokens")
    if not tokens:
        raise NotConnectedError(
            "Google is not connected. Run: python scripts/connect_google.py"
        )

    creds = Credentials.from_authorized_user_info(tokens, scopes=SCOPES)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        cfg.update("google", tokens=_serialize_credentials(creds))
    return creds


def _serialize_credentials(creds) -> dict:
    """Convert a Credentials object to a JSON-serializable dict."""
    return {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": list(creds.scopes) if creds.scopes else SCOPES,
    }


def list_gsc_sites() -> list[dict]:
    """Return the list of GSC sites the connected account has access to."""
    from googleapiclient.discovery import build

    creds = get_credentials()
    service = build("searchconsole", "v1", credentials=creds, cache_discovery=False)
    resp = service.sites().list().execute()
    sites = resp.get("siteEntry", [])
    return [
        {"siteUrl": s.get("siteUrl"), "permissionLevel": s.get("permissionLevel")}
        for s in sites
    ]


def list_ga4_properties() -> list[dict]:
    """Return GA4 properties the user has access to.

    Walks GA4 account summaries via the Admin API.
    """
    from googleapiclient.discovery import build

    creds = get_credentials()
    service = build("analyticsadmin", "v1beta", credentials=creds, cache_discovery=False)

    out: list[dict] = []
    page_token = None
    while True:
        kwargs = {"pageSize": 200}
        if page_token:
            kwargs["pageToken"] = page_token
        resp = service.accountSummaries().list(**kwargs).execute()
        for account in resp.get("accountSummaries", []):
            account_name = account.get("displayName", "")
            for prop in account.get("propertySummaries", []):
                # propertySummary.property is "properties/123456789"
                prop_id = prop.get("property", "").split("/")[-1]
                out.append({
                    "account": account_name,
                    "property_id": prop_id,
                    "display_name": prop.get("displayName", ""),
                })
        page_token = resp.get("nextPageToken")
        if not page_token:
            break
    return out
