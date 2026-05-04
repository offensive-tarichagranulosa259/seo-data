#!/usr/bin/env python3
"""Query Google Analytics 4 using stored OAuth credentials.

Reads the active GA4 property ID from config and runs reports against
the Data API v1beta. Same report surface as the simpler
google-analytics skill, with OAuth instead of a service account.
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lib import config as cfg
from lib import google_auth
from lib.formatting import format_rows


def get_client_and_property():
    from google.analytics.data_v1beta import BetaAnalyticsDataClient

    config = cfg.load_config()
    property_id = config.get("google", {}).get("ga4_property")
    if not property_id:
        raise SystemExit(
            "No GA4 property selected. Run: python scripts/set_property.py --provider ga4"
        )

    creds = google_auth.get_credentials()
    client = BetaAnalyticsDataClient(credentials=creds)
    return client, property_id


def date_range(args) -> tuple[str, str]:
    end = args.end or datetime.now().strftime("%Y-%m-%d")
    start = args.start or (datetime.now() - timedelta(days=args.days)).strftime("%Y-%m-%d")
    return start, end


_GA4_RATE_METRICS = {
    "bounceRate", "engagementRate", "keyEventConversionRate",
    "purchaserConversionRate", "scrolledUsers",
}
_GA4_DURATION_METRICS = {
    "averageSessionDuration", "userEngagementDuration",
}


def format_ga4_value(metric_name: str, value: str) -> str:
    """Format a GA4 metric value: rates as %, durations as Ms, otherwise round."""
    try:
        f = float(value)
    except (ValueError, TypeError):
        return value
    if metric_name in _GA4_RATE_METRICS:
        return f"{f * 100:.1f}%"
    if metric_name in _GA4_DURATION_METRICS:
        if f < 60:
            return f"{f:.1f}s"
        return f"{int(f // 60)}m{int(f % 60):02d}s"
    if f == int(f):
        return str(int(f))
    return f"{f:.2f}"


def run_report(client, property_id, metrics, dimensions, args, order_by_metric=None, desc=True) -> str:
    from google.analytics.data_v1beta.types import (
        RunReportRequest, Metric, Dimension, DateRange, OrderBy
    )

    start, end = date_range(args)
    request = RunReportRequest(
        property=f"properties/{property_id}",
        metrics=[Metric(name=m) for m in metrics],
        dimensions=[Dimension(name=d) for d in dimensions] if dimensions else [],
        date_ranges=[DateRange(start_date=start, end_date=end)],
        limit=args.limit,
    )
    if order_by_metric:
        request.order_bys = [
            OrderBy(metric=OrderBy.MetricOrderBy(metric_name=order_by_metric), desc=desc)
        ]

    resp = client.run_report(request)
    metric_names = [h.name for h in resp.metric_headers]
    headers = [h.name for h in resp.dimension_headers] + metric_names
    rows = []
    for row in resp.rows:
        dim_vals = [dv.value for dv in row.dimension_values]
        met_vals = [format_ga4_value(metric_names[i], mv.value) for i, mv in enumerate(row.metric_values)]
        rows.append(dim_vals + met_vals)
    return format_rows(headers, rows, output=args.output)


def report_overview(client, prop, args):
    return run_report(
        client, prop,
        ["totalUsers", "newUsers", "sessions", "screenPageViews",
         "averageSessionDuration", "engagementRate", "bounceRate"],
        [], args,
    )


def report_pages(client, prop, args):
    return run_report(
        client, prop,
        ["screenPageViews", "totalUsers", "averageSessionDuration"],
        ["pagePath", "pageTitle"], args, order_by_metric="screenPageViews",
    )


def report_sources(client, prop, args):
    return run_report(
        client, prop,
        ["sessions", "totalUsers", "engagementRate", "conversions"],
        ["sessionSource", "sessionMedium"], args, order_by_metric="sessions",
    )


def report_countries(client, prop, args):
    return run_report(
        client, prop,
        ["sessions", "totalUsers", "engagementRate"],
        ["country"], args, order_by_metric="sessions",
    )


def report_devices(client, prop, args):
    return run_report(
        client, prop,
        ["sessions", "totalUsers", "engagementRate"],
        ["deviceCategory"], args, order_by_metric="sessions",
    )


def report_daily(client, prop, args):
    from google.analytics.data_v1beta.types import (
        RunReportRequest, Metric, Dimension, DateRange, OrderBy
    )
    start, end = date_range(args)
    request = RunReportRequest(
        property=f"properties/{prop}",
        metrics=[Metric(name=m) for m in ["totalUsers", "sessions", "screenPageViews"]],
        dimensions=[Dimension(name="date")],
        date_ranges=[DateRange(start_date=start, end_date=end)],
        limit=max(args.days or 30, args.limit),
        order_bys=[OrderBy(dimension=OrderBy.DimensionOrderBy(dimension_name="date"), desc=False)],
    )
    resp = client.run_report(request)
    metric_names = [h.name for h in resp.metric_headers]
    headers = [h.name for h in resp.dimension_headers] + metric_names
    rows = []
    for row in resp.rows:
        dim_vals = [dv.value for dv in row.dimension_values]
        met_vals = [format_ga4_value(metric_names[i], mv.value) for i, mv in enumerate(row.metric_values)]
        rows.append(dim_vals + met_vals)
    return format_rows(headers, rows, output=args.output)


def report_realtime(client, prop, args):
    from google.analytics.data_v1beta.types import (
        RunRealtimeReportRequest, Metric, Dimension
    )
    request = RunRealtimeReportRequest(
        property=f"properties/{prop}",
        metrics=[Metric(name="activeUsers")],
        dimensions=[Dimension(name="unifiedScreenName")],
        limit=args.limit,
    )
    resp = client.run_realtime_report(request)
    headers = [h.name for h in resp.dimension_headers] + [h.name for h in resp.metric_headers]
    rows = [
        [dv.value for dv in row.dimension_values] + [mv.value for mv in row.metric_values]
        for row in resp.rows
    ]
    if not rows:
        return "No active users right now."
    return format_rows(headers, rows, output=args.output)


def report_custom(client, prop, args):
    if not args.metrics:
        raise SystemExit("Error: --metrics required for custom report")
    metrics = [m.strip() for m in args.metrics.split(",")]
    dimensions = [d.strip() for d in args.dimensions.split(",")] if args.dimensions else []
    return run_report(
        client, prop, metrics, dimensions, args,
        order_by_metric=metrics[0],
    )


REPORTS = {
    "overview": report_overview,
    "pages": report_pages,
    "sources": report_sources,
    "countries": report_countries,
    "devices": report_devices,
    "daily": report_daily,
    "realtime": report_realtime,
    "custom": report_custom,
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Query Google Analytics 4 data")
    parser.add_argument("--report", required=True, choices=REPORTS.keys())
    parser.add_argument("--days", type=int, default=30)
    parser.add_argument("--start", help="Start date YYYY-MM-DD")
    parser.add_argument("--end", help="End date YYYY-MM-DD")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--output", choices=["table", "json", "csv"], default="table")
    parser.add_argument("--metrics", help="Comma-separated metrics (custom report)")
    parser.add_argument("--dimensions", help="Comma-separated dimensions (custom report)")
    args = parser.parse_args()

    try:
        client, prop = get_client_and_property()
        result = REPORTS[args.report](client, prop, args)
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
