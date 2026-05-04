#!/usr/bin/env python3
"""Query Bing Webmaster Tools using a stored API key.

Bing API quirks this script papers over:

- Dates come back as `/Date(1767945600000-0800)/` (millis since epoch with
  timezone suffix), so we parse with a regex that tolerates the suffix.
- `GetQueryStats` and `GetPageStats` both return rows of `QueryStats` type
  with a `Query` field. For GetPageStats the `Query` field actually holds
  the page URL. Both need aggregation across the date window.
- The keyword research endpoint is `GetKeywordStats` (not `GetKeywords`).
- The Bing API returns up to ~6 months of fixed history, so `--days`
  is honored client-side via row filtering.
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lib import bing_auth
from lib.formatting import format_rows


_BING_DATE_RE = re.compile(r"/Date\((\d+)(?:[-+]\d{4})?\)/")


def parse_bing_date(value: Any) -> str:
    if not isinstance(value, str):
        return str(value)
    m = _BING_DATE_RE.match(value)
    if not m:
        return value
    ts = datetime.fromtimestamp(int(m.group(1)) / 1000, tz=timezone.utc)
    return ts.strftime("%Y-%m-%d")


def _row_date(row: dict) -> datetime | None:
    raw = row.get("Date")
    if not isinstance(raw, str):
        return None
    m = _BING_DATE_RE.match(raw)
    if not m:
        return None
    return datetime.fromtimestamp(int(m.group(1)) / 1000, tz=timezone.utc)


def filter_by_days(rows: list[dict], days: int) -> list[dict]:
    cutoff = datetime.now(tz=timezone.utc) - timedelta(days=days)
    out = []
    for r in rows:
        d = _row_date(r)
        if d is not None and d >= cutoff:
            out.append(r)
    return out


def aggregate_by_query(rows: list[dict]) -> list[dict]:
    """Collapse per-(query, date) rows into per-query totals.

    Impressions and Clicks are summed. AvgImpressionPosition is averaged
    weighted by Impressions. AvgClickPosition is averaged weighted by
    Clicks (only over rows that actually had clicks; -1 is Bing's sentinel
    for "no clicks at this position").
    """
    agg: dict[str, dict] = {}
    for r in rows:
        q = r.get("Query") or ""
        if not q:
            continue
        bucket = agg.setdefault(q, {
            "Impressions": 0,
            "Clicks": 0,
            "_imp_pos_sum": 0.0,
            "_clk_pos_sum": 0.0,
            "_clk_count": 0,
        })
        imp = r.get("Impressions", 0) or 0
        clk = r.get("Clicks", 0) or 0
        imp_pos = r.get("AvgImpressionPosition", 0) or 0
        clk_pos = r.get("AvgClickPosition", -1)
        bucket["Impressions"] += imp
        bucket["Clicks"] += clk
        bucket["_imp_pos_sum"] += imp * imp_pos
        if clk > 0 and clk_pos is not None and clk_pos != -1:
            bucket["_clk_pos_sum"] += clk * clk_pos
            bucket["_clk_count"] += clk

    out: list[dict] = []
    for q, b in agg.items():
        avg_imp_pos = (b["_imp_pos_sum"] / b["Impressions"]) if b["Impressions"] else 0
        avg_clk_pos = (b["_clk_pos_sum"] / b["_clk_count"]) if b["_clk_count"] else None
        out.append({
            "Query": q,
            "Impressions": b["Impressions"],
            "Clicks": b["Clicks"],
            "AvgImpressionPosition": round(avg_imp_pos, 1),
            "AvgClickPosition": round(avg_clk_pos, 1) if avg_clk_pos is not None else "-",
        })
    return out


def report_queries(args) -> str:
    raw = bing_auth.call("GetQueryStats") or []
    raw = filter_by_days(raw, args.days)
    rows = aggregate_by_query(raw)
    rows.sort(key=lambda r: r["Clicks"], reverse=True)
    rows = rows[: args.limit]

    headers = ["Query", "Impressions", "Clicks", "AvgImpressionPosition", "AvgClickPosition"]
    formatted = [[r[h] for h in headers] for r in rows]
    return format_rows(headers, formatted, output=args.output)


def report_pages(args) -> str:
    """GetPageStats returns rows with the URL in the `Query` field. We
    aggregate by URL and present the column as 'Page' for clarity."""
    raw = bing_auth.call("GetPageStats") or []
    raw = filter_by_days(raw, args.days)
    rows = aggregate_by_query(raw)
    rows.sort(key=lambda r: r["Clicks"], reverse=True)
    rows = rows[: args.limit]

    headers = ["Page", "Impressions", "Clicks", "AvgImpressionPosition", "AvgClickPosition"]
    formatted = []
    for r in rows:
        formatted.append([
            r["Query"], r["Impressions"], r["Clicks"],
            r["AvgImpressionPosition"], r["AvgClickPosition"],
        ])
    return format_rows(headers, formatted, output=args.output)


def report_traffic(args) -> str:
    """GetRankAndTrafficStats only exposes Date / Impressions / Clicks.
    No position fields, despite the endpoint name."""
    raw = bing_auth.call("GetRankAndTrafficStats") or []
    raw = filter_by_days(raw, args.days)
    raw.sort(key=lambda r: _row_date(r) or datetime.min.replace(tzinfo=timezone.utc))

    headers = ["Date", "Impressions", "Clicks", "CTR"]
    formatted = []
    for r in raw:
        impr = r.get("Impressions", 0) or 0
        clks = r.get("Clicks", 0) or 0
        ctr = f"{(clks / impr * 100):.2f}%" if impr else "-"
        formatted.append([parse_bing_date(r.get("Date", "")), impr, clks, ctr])
    return format_rows(headers, formatted, output=args.output)


def report_crawl(args) -> str:
    raw = bing_auth.call("GetCrawlStats") or []
    raw = filter_by_days(raw, args.days)
    raw.sort(key=lambda r: _row_date(r) or datetime.min.replace(tzinfo=timezone.utc))

    headers = [
        "Date", "CrawledPages", "InIndex", "InLinks",
        "Code2xx", "Code301", "Code4xx", "Code5xx",
        "BlockedByRobotsTxt", "DnsFailures", "CrawlErrors",
    ]
    formatted = []
    for r in raw:
        formatted.append([
            parse_bing_date(r.get("Date", "")),
            r.get("CrawledPages", 0),
            r.get("InIndex", 0),
            r.get("InLinks", 0),
            r.get("Code2xx", 0),
            r.get("Code301", 0),
            r.get("Code4xx", 0),
            r.get("Code5xx", 0),
            r.get("BlockedByRobotsTxt", 0),
            r.get("DnsFailures", 0),
            r.get("CrawlErrors", 0),
        ])
    return format_rows(headers, formatted, output=args.output)


def report_keywords(args) -> str:
    """Keyword research via GetKeywordStats — broad + narrow match
    impressions for a given keyword, returned per-date. We aggregate
    across the requested window."""
    if not args.query:
        raise SystemExit("Error: --query required for keywords report")

    params: dict[str, Any] = {
        "q": args.query,
        "country": args.country or "us",
        "language": args.language or "en-US",
    }
    raw = bing_auth.call("GetKeywordStats", params=params) or []

    if not raw:
        return f"No keyword data found for '{args.query}'."

    total_impr = 0
    total_broad = 0
    dates_seen: list[datetime] = []
    for r in raw:
        d = _row_date(r)
        if d:
            dates_seen.append(d)
        total_impr += r.get("Impressions", 0) or 0
        total_broad += r.get("BroadImpressions", 0) or 0

    headers = ["Keyword", "Country", "Language", "Impressions", "BroadImpressions", "DataPoints", "Range"]
    if dates_seen:
        date_range = f"{min(dates_seen).strftime('%Y-%m-%d')} to {max(dates_seen).strftime('%Y-%m-%d')}"
    else:
        date_range = "-"
    rows = [[
        args.query,
        params["country"],
        params["language"],
        total_impr,
        total_broad,
        len(raw),
        date_range,
    ]]
    return format_rows(headers, rows, output=args.output)


REPORTS = {
    "queries": report_queries,
    "pages": report_pages,
    "traffic": report_traffic,
    "crawl": report_crawl,
    "keywords": report_keywords,
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Query Bing Webmaster Tools")
    parser.add_argument("--report", required=True, choices=REPORTS.keys())
    parser.add_argument("--days", type=int, default=30, help="Client-side date filter window")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--output", choices=["table", "json", "csv"], default="table")
    parser.add_argument("--query", help="Search term (keywords report)")
    parser.add_argument("--country", help="Country code (keywords report, default 'us')")
    parser.add_argument("--language", help="Language code (keywords report, default 'en-US')")
    args = parser.parse_args()

    try:
        result = REPORTS[args.report](args)
        print(result)
    except bing_auth.NotConnectedError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
