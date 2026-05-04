---
name: seo-data
description: Direct access to Google Search Console, Google Analytics 4, and Bing Webmaster Tools data via OAuth/API key. Use whenever the user asks SEO, search performance, organic traffic, ranking, impressions, clicks, CTR, conversions, traffic source, landing page, or analytics questions and wants real numbers from their own properties — not generic advice. Triggers on "SEO", "search console", "GSC", "GA4", "analytics", "Bing webmaster", "rankings", "keywords", "impressions", "clicks", "organic traffic", "traffic drop", "top pages", "top queries". Works with any subset of the three providers the user has connected.
---

# seo-data — Unified GSC / GA4 / Bing Webmaster Skill

Provides direct, authenticated access to a user's own SEO data across three platforms. Each provider is independent: the user may have one, two, or all three connected. **Always degrade gracefully** — never fail an answer because one provider is missing; use what's available and tell the user what you skipped.

## Provider matrix

| Provider | Auth | What it answers |
|---|---|---|
| GSC (Google Search Console) | OAuth | What people *searched* for on Google before reaching the site (queries, impressions, clicks, CTR, position) |
| GA4 (Google Analytics 4) | OAuth (same Google account) | What users *did* on the site (sessions, page views, conversions, traffic sources, geography) |
| Bing Webmaster Tools | API key | Same questions as GSC, but for Bing search |

GSC ≠ GA4. GSC is "what Google's index thinks about your site." GA4 is "what visitors do once they land." They complement each other; cross-referencing them is one of the highest-value workflows this skill enables.

## Vocabulary mapping (which provider for which word)

When the user asks a question, route on these terms:

| Word in user's question | Provider |
|---|---|
| traffic, visits, visitors, sessions, pageviews, page views, users, conversions, bounce rate, engagement | **GA4** |
| impressions, rankings, ranks, ranking position, query, queries, keyword (Google), CTR (search), search performance, SERP | **GSC** (Google) or **Bing** (if specified) |
| crawl, indexed, sitemap, robots | **GSC** or **Bing** |

**When the user mixes both senses in one question** ("top queries and which pages got the most traffic", "rankings vs. visits", "search performance and conversions"), call the relevant providers **in parallel** and present both sides. Don't collapse "traffic" into impression counts — those are different concepts and SEOs will notice.

**When the user says "search" without specifying engine**, default to GSC unless Bing was explicitly mentioned earlier in the conversation or unless GSC isn't connected.

## First step: check what's connected

If you don't already know the connection state from earlier in the session, run:

```bash
python scripts/status.py
```

Output is JSON with `google.connected`, `gsc.site`, `ga4.property`, `bing.connected`, `bing.site`. Use this to decide which queries are possible.

If a provider the user is asking about isn't connected, offer to connect it before failing. Don't silently skip.

## Connecting providers

### Google (GSC + GA4)

```bash
python scripts/connect_google.py [--client-secrets PATH]
```

This opens the user's browser for OAuth consent, then prompts them (via stdout — Claude relays to user) to pick a GSC site and a GA4 property from the lists their account has access to.

Prerequisites the user must do once:
1. Create a Google Cloud OAuth client (Desktop app type) — README has the 5-minute walkthrough
2. Save the JSON to `~/.seo-data/google_client.json` (default path) OR pass `--client-secrets`

If `google_client.json` is missing, the script prints a clear error pointing the user to the README. Relay that to the user; don't try to work around it.

### Bing Webmaster

```bash
python scripts/connect_bing.py --api-key <KEY>
```

Validates the key, lists the user's verified sites, prompts for site selection. The user gets the API key from bing.com/webmasters → Settings → API Access.

If the user gives you their key in chat, pass it via `--api-key`. Don't echo the key back in your response.

## Switching properties / accounts

```bash
python scripts/set_property.py --provider gsc      # pick a different GSC site
python scripts/set_property.py --provider ga4      # pick a different GA4 property
python scripts/set_property.py --provider bing     # pick a different Bing site
python scripts/disconnect.py google                # full Google disconnect (clears tokens)
python scripts/disconnect.py bing                  # clear Bing API key
```

To reconnect a different account: `disconnect.py google` then `connect_google.py`.

## Querying data

All query scripts support `--output table|json|csv` (default `table`) and `--days N` (default 30).

### GSC — `python scripts/gsc_query.py --report <type>`

| Report | Dimensions returned |
|---|---|
| `queries` | top search queries |
| `pages` | top landing pages |
| `countries` | performance by country |
| `devices` | desktop / mobile / tablet |
| `daily` | day-by-day trend |
| `query-pages` | which pages rank for which queries |
| `custom` | pass `--dimensions "query,page"` and optional filter |

Common options: `--limit N`, `--start YYYY-MM-DD`, `--end YYYY-MM-DD`, `--filter-dimension`, `--filter-operator`, `--filter-expression`. GSC data has a ~3-day delay.

### GA4 — `python scripts/ga4_query.py --report <type>`

| Report | What it returns |
|---|---|
| `overview` | totalUsers, sessions, pageViews, engagement, bounce |
| `pages` | top pages by views |
| `sources` | sessionSource × sessionMedium |
| `countries` | by country |
| `devices` | desktop / mobile / tablet |
| `daily` | day-by-day trend |
| `realtime` | active users in last 30 minutes |
| `custom` | pass `--metrics` and `--dimensions` |

### Bing — `python scripts/bing_query.py --report <type>`

| Report | What it returns |
|---|---|
| `queries` | Top search queries -- aggregated impressions, clicks, weighted avg position across `--days` window |
| `pages` | Top pages -- same aggregation as queries, but URL is the dimension |
| `traffic` | Daily impressions, clicks, CTR (Bing does not return position in this endpoint) |
| `crawl` | Daily crawl activity -- pages crawled, status code breakdown (2xx/301/4xx/5xx), in-index, in-links, robots.txt blocks, DNS failures, errors |
| `keywords` | Keyword research for a specific term (requires `--query`, optional `--country` default `us`, `--language` default `en-US`). Returns total narrow + broad match impressions over Bing's available ~6-month window |

Bing returns up to ~6 months of fixed history. `--days` is honored client-side by filtering rows. The `queries` and `pages` reports aggregate per-(item, date) rows into per-item totals using impression-weighted position averaging.

Bing API quirk to be aware of: `GetPageStats` returns rows where the URL is in the `Query` field (not `Page`). The script handles this internally; the table column is labelled "Page" for the user.

## Workflow patterns

**"How is SEO performing?"** — Run GSC `daily` and GA4 `overview` in parallel. If Bing is connected, also run Bing `traffic`.

**"Diagnose this traffic drop."** — Compare two periods. Get GSC `daily` and `queries` for current vs prior period (use `--start`/`--end`). Look for queries that lost impressions or position. Cross-check GA4 `sources` to see if it's organic-specific or broader.

**"Which content is underperforming?"** — GSC `pages` + GA4 `pages`. Pages with high impressions but low clicks (GSC) = title/meta-description issue. Pages with high pageviews but low engagement time (GA4) = content issue.

**"What should we write next?"** — GSC `queries` with `--filter-operator notContains` to find queries the user ranks for that *aren't* in any current page title. Combine with Bing `keywords` for keyword volume signal.

## Important behaviors

- **Never fabricate numbers.** If a query fails, surface the error and offer to retry or reconnect.
- **Don't echo API keys or refresh tokens** in responses, even if the user shared them.
- **Convert relative dates** ("last week", "Q1") to explicit `--start`/`--end` so the user can verify.
- **Note GSC's 3-day delay** when the user asks about "yesterday" or "today."
- **GSC uses CTR as decimal** (0.05 = 5%); the script formats it as a percentage in the output already.
- **Position is 1-indexed**, lower is better.
- If only one provider is connected and the user asks something only another provider can answer, say so clearly and offer to connect the missing one.
