# seo-data

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

**A Claude Skill for direct, authenticated SEO data access — Google Search Console, Google Analytics 4, and Bing Webmaster Tools in one place.**

Most "SEO skills" you'll find are prompt instructions that tell Claude how to *audit* a site. This one connects Claude to your **actual data**: query stats, traffic, conversions, crawl health. You ask a question, Claude pulls the numbers and answers from the source.

The skill works with whatever subset you've connected. Have only GSC? You get GSC. Have all three? Claude can cross-reference search performance against on-site behavior and Bing visibility in a single answer.

---

## Features

- **Three providers, one skill** -- Google Search Console (OAuth), Google Analytics 4 (OAuth), Bing Webmaster Tools (API key)
- **OAuth done right** -- loopback flow with refresh tokens, multi-account support, switch properties without reconnecting
- **Graceful degradation** -- if a provider isn't connected, the skill skips it and tells the user, instead of failing the answer
- **Multi-property** -- pick which GSC site, GA4 property, or Bing site to query; switch any time
- **No telemetry** -- tokens and API keys live only in `~/.seo-data/`; nothing leaves your machine except calls to the official APIs
- **Plain Python** -- the skill is a folder of standalone scripts, easy to fork, audit, or extend
- **Built-in report library** -- top queries, top pages, traffic sources, daily trends, device breakdown, custom dimensions, plus Bing-specific reports (crawl, keyword research)

## Quick Start

### Prerequisites

- [Python 3.10+](https://www.python.org/downloads/)
- A working [Claude Code](https://claude.com/claude-code) install (or any agent that supports Claude Skills)
- Read access to at least one of: Google Search Console, Google Analytics 4, Bing Webmaster Tools

### Two ways to install

**Option A — Let an AI agent do it for you (recommended)**

If you have Claude Code, Cursor, Cline, Aider, or any other AI coding agent, this is by far the easiest path. Clone the repo, open the agent inside it, and say:

> "Read AGENT.md and set this up for me."

The agent will install dependencies, copy the skill into the right place, walk you through the Google Cloud Console click-by-click, ask you for your Bing API key, and verify everything works. It only stops to ask you for the things only you can do (clicking buttons in your browser, pasting credentials).

See [AGENT.md](AGENT.md) for the full agent runbook.

**Option B — Do it yourself**

Follow the human walkthrough in [docs/SETUP.md](docs/SETUP.md). It covers every step explicitly:

1. **Install the skill** — clone the repo, `pip install -r requirements.txt`, copy into your Claude skills directory
2. **Connect Bing** (5 minutes) — get an API key, run one command
3. **Connect Google** (~10 minutes) — create a Google Cloud project, enable two APIs, configure an OAuth consent screen, download an OAuth client JSON, run the connect script, consent in the browser
4. **Pick which property to use** — GSC site, GA4 property, Bing site
5. **Verify in Claude** — ask a real SEO question and watch it work

Both paths land you at the same place: a `seo-data` skill installed, all your providers connected, and Claude ready to query your real data.

### Ask Claude

Once connected, the skill triggers automatically on SEO/analytics questions:

> "What were our top queries last week?"
> "Which pages got the most traffic from organic search?"
> "Show me Bing impressions trend for the last 30 days."
> "Cross-reference GSC queries with GA4 conversions for the same landing pages."
> "Diagnose this traffic drop."

Claude figures out which provider(s) can answer, calls the relevant scripts, and presents the data.

## Manual usage

The skill is just a folder of Python scripts. You can call them directly without Claude:

```bash
cd ~/.claude/skills/seo-data

# What's connected?
python scripts/status.py

# Connect Google (opens browser)
python scripts/connect_google.py

# Connect Bing
python scripts/connect_bing.py --api-key <KEY>

# Switch property
python scripts/set_property.py --provider gsc --site https://example.com/
python scripts/set_property.py --provider ga4 --property 123456789

# Disconnect
python scripts/disconnect.py google
python scripts/disconnect.py bing

# Run a report
python scripts/gsc_query.py --report queries --days 30 --limit 20
python scripts/ga4_query.py --report sources --days 7
python scripts/bing_query.py --report traffic --days 30
```

All query scripts support `--output table|json|csv` (default `table`).

## Reports

### Google Search Console — `gsc_query.py`

| Report | Returns |
|---|---|
| `queries` | Top search queries (clicks, impressions, CTR, position) |
| `pages` | Top landing pages |
| `countries` | Performance by country |
| `devices` | Desktop / mobile / tablet split |
| `daily` | Day-by-day trend |
| `query-pages` | Which pages rank for which queries |
| `custom` | Pass `--dimensions` and optional filter |

### Google Analytics 4 — `ga4_query.py`

| Report | Returns |
|---|---|
| `overview` | Users, sessions, page views, engagement, bounce |
| `pages` | Top pages by views |
| `sources` | Traffic sources (source × medium) |
| `countries` | Geographic breakdown |
| `devices` | Device category split |
| `daily` | Day-by-day trend |
| `realtime` | Active users in last 30 minutes |
| `custom` | Pass `--metrics` and `--dimensions` |

### Bing Webmaster Tools — `bing_query.py`

| Report | Returns |
|---|---|
| `queries` | Top search queries (aggregated across the date window) |
| `pages` | Top pages |
| `traffic` | Daily impressions, clicks, CTR |
| `crawl` | Daily crawl: pages crawled, status code breakdown, in-index, in-links, errors |
| `keywords` | Keyword research for a term (requires `--query`) |

## Architecture

```
seo-data/
├── SKILL.md              # Claude-facing skill instructions
├── README.md             # This file
├── requirements.txt
├── lib/
│   ├── config.py         # Token + property storage at ~/.seo-data/
│   ├── google_auth.py    # OAuth loopback flow + GSC/GA4 listing
│   ├── bing_auth.py      # API key validation + Bing API caller
│   └── formatting.py     # Shared table / JSON / CSV output
├── scripts/
│   ├── status.py         # JSON of connection state
│   ├── connect_google.py # OAuth flow
│   ├── connect_bing.py   # API key entry
│   ├── disconnect.py     # Clear a provider
│   ├── set_property.py   # Pick GSC site / GA4 property / Bing site
│   ├── gsc_query.py      # Search Console reports
│   ├── ga4_query.py      # GA4 reports
│   └── bing_query.py     # Bing Webmaster reports
├── docs/
│   └── SETUP.md          # Full human walkthrough (install + all 3 providers)
└── AGENT.md              # Runbook for AI coding agents to automate setup
```

## Where credentials live

All under `~/.seo-data/` (or `%USERPROFILE%\.seo-data\` on Windows):

- `google_client.json` -- your OAuth client config (you provide this once)
- `config.json` -- refresh tokens, API keys, selected properties

On POSIX systems, the directory is created with `0700` permissions. The skill makes API calls only to:

- `oauth2.googleapis.com` (token refresh)
- `searchconsole.googleapis.com` (GSC)
- `analyticsadmin.googleapis.com` (GA4 property listing)
- `analyticsdata.googleapis.com` (GA4 reports)
- `ssl.bing.com/webmaster/api.svc/json/` (Bing)

No third-party servers, no telemetry.

## Documentation

| Document | Description |
|----------|-------------|
| [Setup Guide](docs/SETUP.md) | Full human walkthrough -- install, connect all 3 providers, troubleshooting |
| [Agent Runbook](AGENT.md) | Instructions for AI coding agents to automate setup end-to-end |
| [Skill Reference](SKILL.md) | How Claude uses the skill -- workflows, behavior rules |

## Contributing

Contributions are welcome but this project is maintained on a best-effort basis. PRs may not be reviewed immediately. See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

Apache 2.0 -- see [LICENSE](LICENSE) for details.
