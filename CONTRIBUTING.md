# Contributing to seo-data

Thanks for your interest in contributing!

## Getting Started

1. Fork the repo and clone it locally
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # or venv\Scripts\activate on Windows
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. (Optional) Install dev tooling:
   ```bash
   pip install ruff pytest
   ```

To work on the skill locally, point Claude at your fork by symlinking or copying it into your skills directory:

```bash
# macOS / Linux
ln -s "$(pwd)" ~/.claude/skills/seo-data

# Windows (run as admin or with developer mode enabled)
New-Item -ItemType SymbolicLink -Path "$env:USERPROFILE\.claude\skills\seo-data" -Target (Get-Location)
```

## Development

### Code Style

We use [ruff](https://github.com/astral-sh/ruff) for linting and formatting:

```bash
ruff check .
ruff format .
```

### Project Structure

- `SKILL.md` -- Claude-facing skill instructions
- `lib/` -- shared code (config, auth, formatting)
- `scripts/` -- one entry point per skill action
- `docs/` -- user-facing documentation

Each script in `scripts/` is a standalone CLI. Keep them small and orthogonal -- don't combine "connect" and "query" into one script.

### Testing changes

The skill talks to live APIs, so most testing is manual against your own GSC / GA4 / Bing accounts. When adding a new report:

1. Run the script manually with `--output json` and verify the shape
2. Add the report to `SKILL.md` so Claude knows it exists
3. Add a row to the relevant table in `README.md`

For OAuth changes, test the full flow on a clean `~/.seo-data/` directory.

## Submitting Changes

1. Create a feature branch from `master`
2. Make your changes with focused commits
3. Ensure linting is clean (`ruff check .`)
4. Open a pull request describing what changed and why

## Reporting Issues

Open an issue at [github.com/anthonylee991/seo-data/issues](https://github.com/anthonylee991/seo-data/issues) with:

- What you expected to happen
- What actually happened
- Steps to reproduce
- Python version, OS, and which provider(s) you had connected
- Redact any tokens, API keys, or property IDs before posting

## Areas for Contribution

- Additional GSC / GA4 / Bing report types
- Cross-provider report scripts (e.g. correlating GSC queries with GA4 landing-page behavior)
- Improved error messages on common OAuth failure modes
- Additional output formats (Markdown tables, HTML)
- Tests with mocked API responses
- Documentation improvements

## License

By contributing, you agree that your contributions will be licensed under the Apache License 2.0.
