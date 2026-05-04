#!/usr/bin/env python3
"""Query Google Search Console using stored OAuth credentials.

Reads the active GSC site URL from config and runs Search Analytics
reports against it. Same report surface as the simpler
google-search-console skill but with multi-account OAuth instead of a
single service account.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lib import config as cfg
from lib import google_auth
from lib.formatting import format_rows


def get_service_and_site():
    from googleapiclient.discovery import build

    config = cfg.load_config()
    site = config.get("google", {}).get("gsc_site")
    if not site:
        raise SystemExit(
            "No GSC site selected. Run: python scripts/set_property.py --provider gsc"
        )

    creds = google_auth.get_credentials()
    service = build("searchconsole", "v1", credentials=creds, cache_discovery=False)
    return service, site


def date_range(args) -> tuple[str, str]:
    end = args.end or (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")
    start = args.start or (datetime.now() - timedelta(days=args.days)).strftime("%Y-%m-%d")
    return start, end


def build_body(dimensions, args, filter_dimension=None, filter_operator=None, filter_expression=None):
    start, end = date_range(args)
    body: dict = {
        "startDate": start,
        "endDate": end,
        "dimensions": dimensions,
        "rowLimit": args.limit,
    }
    if filter_dimension and filter_expression:
        body["dimensionFilterGroups"] = [{
            "filters": [{
                "dimension": filter_dimension,
                "operator": filter_operator or "contains",
                "expression": filter_expression,
            }]
        }]
    return body


def run_report(service, site, dimensions, args, **filters) -> str:
    body = build_body(dimensions, args, **filters)
    resp = service.searchanalytics().query(siteUrl=site, body=body).execute()
    rows = resp.get("rows", [])

    headers = list(dimensions) + ["clicks", "impressions", "ctr", "position"]
    formatted: list[list] = []
    for r in rows:
        keys = r.get("keys", [])
        formatted.append([
            *keys,
            r.get("clicks", 0),
            r.get("impressions", 0),
            f"{r.get('ctr', 0) * 100:.1f}%",
            f"{r.get('position', 0):.1f}",
        ])
    return format_rows(headers, formatted, output=args.output)


REPORTS = {
    "queries": lambda s, site, a: run_report(s, site, ["query"], a),
    "pages": lambda s, site, a: run_report(s, site, ["page"], a),
    "countries": lambda s, site, a: run_report(s, site, ["country"], a),
    "devices": lambda s, site, a: run_report(s, site, ["device"], a),
    "daily": lambda s, site, a: run_report(s, site, ["date"], a),
    "query-pages": lambda s, site, a: run_report(s, site, ["query", "page"], a),
}


def report_custom(service, site, args) -> str:
    if not args.dimensions:
        raise SystemExit("Error: --dimensions required for custom report (comma-separated)")
    dims = [d.strip() for d in args.dimensions.split(",")]
    return run_report(
        service, site, dims, args,
        filter_dimension=args.filter_dimension,
        filter_operator=args.filter_operator,
        filter_expression=args.filter_expression,
    )


REPORTS["custom"] = report_custom


def main() -> int:
    parser = argparse.ArgumentParser(description="Query Google Search Console data")
    parser.add_argument("--report", required=True, choices=REPORTS.keys())
    parser.add_argument("--days", type=int, default=30)
    parser.add_argument("--start", help="Start date YYYY-MM-DD (overrides --days)")
    parser.add_argument("--end", help="End date YYYY-MM-DD (default: 3 days ago)")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--output", choices=["table", "json", "csv"], default="table")
    parser.add_argument("--dimensions", help="Comma-separated (custom report)")
    parser.add_argument("--filter-dimension")
    parser.add_argument("--filter-operator", default="contains",
                        choices=["contains", "equals", "notContains", "notEquals"])
    parser.add_argument("--filter-expression")
    args = parser.parse_args()

    try:
        service, site = get_service_and_site()
        result = REPORTS[args.report](service, site, args)
        print(result)
    except google_auth.NotConnectedError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
