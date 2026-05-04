# Setup Guide

This guide walks you through everything from a fresh install to seeing real data in Claude. Read it top-to-bottom the first time, even if some steps feel obvious.

It covers all three providers — Google Search Console, Google Analytics 4, and Bing Webmaster Tools. You can connect any subset; if you only have Bing, skip the Google sections and the skill will still work.

**Total time the first time:** about 15 minutes if you connect all three providers. About 5 minutes for Bing alone.

> ⚡ **Have an AI coding agent?** If you're using Claude Code, Cursor, Cline, Aider, or any other agent that can read files and run commands inside the cloned repo, point it at [AGENT.md](../AGENT.md) instead of this file. The agent will automate every step that doesn't require you to click in a browser.

---

## Table of contents

- [Part 1 — Install the skill](#part-1--install-the-skill)
- [Part 2 — Connect Bing Webmaster Tools](#part-2--connect-bing-webmaster-tools) (5 minutes, easiest)
- [Part 3 — Connect Google (GSC + GA4)](#part-3--connect-google-gsc--ga4) (~10 minutes)
- [Part 4 — Pick a property](#part-4--pick-a-property)
- [Part 5 — Verify in Claude](#part-5--verify-in-claude)
- [Troubleshooting](#troubleshooting)

---

## Part 1 — Install the skill

### 1.1 Prerequisites

Make sure you have these on your machine:

- **Python 3.10 or newer.** Open a terminal and run `python --version`. If you see something older than 3.10 (or "command not found"), install from [python.org/downloads](https://www.python.org/downloads/).
- **Git** (only needed if you want to `git clone`; you can also download the repo as a ZIP).
- **Claude Code** (or another agent that supports Claude Skills). If you don't have it yet, follow the install instructions at [claude.com/claude-code](https://claude.com/claude-code).

### 1.2 Get the repo

Pick one of:

```bash
# Option A — Clone it
git clone https://github.com/anthonylee991/seo-data.git
cd seo-data

# Option B — Download the ZIP from GitHub and unzip it somewhere
```

### 1.3 Install Python dependencies

Inside the repo folder:

```bash
pip install -r requirements.txt
```

If you get a "permission denied" error on macOS / Linux, try `pip install --user -r requirements.txt`.

If the command isn't found, try `python -m pip install -r requirements.txt`.

### 1.4 Install the skill into Claude

Claude reads skills from `~/.claude/skills/` (Linux/macOS) or `%USERPROFILE%\.claude\skills\` (Windows). Copy the repo contents into a folder called `seo-data` inside that directory.

**On Windows (PowerShell):**

```powershell
xcopy /E /I /Y . "$env:USERPROFILE\.claude\skills\seo-data"
```

**On macOS / Linux:**

```bash
cp -r . ~/.claude/skills/seo-data
```

### 1.5 Verify the install

Run the status script. It should print JSON showing nothing is connected yet (which is correct — we haven't done credentials yet).

**Windows:**

```powershell
python "$env:USERPROFILE\.claude\skills\seo-data\scripts\status.py"
```

**macOS / Linux:**

```bash
python ~/.claude/skills/seo-data/scripts/status.py
```

You should see something like:

```json
{
  "config_dir": "/Users/yourname/.seo-data",
  "google": { "connected": false, "client_secrets_present": false },
  "gsc": { "ready": false, "site": null },
  "ga4": { "ready": false, "property": null },
  "bing": { "connected": false, "ready": false, "site": null }
}
```

If you see that JSON, the install is working. Move on to credentials.

If you got an error, jump to [Troubleshooting](#troubleshooting).

---

## Part 2 — Connect Bing Webmaster Tools

This is the easiest provider — it's just an API key. Skip this section if you don't use Bing for SEO.

### 2.1 Get your Bing API key

1. Open [bing.com/webmasters](https://www.bing.com/webmasters) in your browser.
2. Sign in with the Microsoft account that owns your Bing Webmaster Tools setup.
3. Click the **gear icon** (Settings) in the top-right corner.
4. Click **API Access** in the left sidebar.
5. You'll see a long alphanumeric string — that's your API key. Click **Copy**.

If you don't see "API Access," your account might not have admin permission on the BWT property. The owner of the property needs to grant you the role.

### 2.2 Run the connect script

Replace `<YOUR_KEY>` with the key you copied.

**Windows:**

```powershell
python "$env:USERPROFILE\.claude\skills\seo-data\scripts\connect_bing.py" --api-key <YOUR_KEY>
```

**macOS / Linux:**

```bash
python ~/.claude/skills/seo-data/scripts/connect_bing.py --api-key <YOUR_KEY>
```

You should see a JSON response listing the verified Bing sites your account can access. If you only have one site, the skill will auto-select it. If you have multiple, you'll need to pick one in [Part 4](#part-4--pick-a-property).

### 2.3 What if it fails?

- **`401` or `403`** — the API key is wrong, expired, or your account doesn't have permission. Generate a new key from BWT.
- **Network error** — you're behind a firewall blocking `ssl.bing.com`, or you're offline.
- **No verified sites** — your BWT account hasn't verified any sites yet. Verify a site in BWT first, then re-run.

---

## Part 3 — Connect Google (GSC + GA4)

This is the longer setup — about 10 minutes — because Google requires you to create your own OAuth client. **You only do this once.** After that, you can connect any number of GSC sites or GA4 properties through the same client.

> **Why this is required:** `webmasters.readonly` and `analytics.readonly` are Google "restricted scopes." Apps that use them and have more than ~100 users have to go through Google verification + an annual security assessment. To avoid that, every user creates their own OAuth client in their own Google Cloud project. Your tokens stay scoped to your project, you control which Google account grants access, and Google never has to verify a shared third-party app.

### 3.1 Open Google Cloud Console

Go to [console.cloud.google.com](https://console.cloud.google.com/) and sign in with the Google account that owns the GSC sites and GA4 properties you want to query. Use the same account for both — that's the whole point.

If this is your first time using Google Cloud, accept the terms and proceed. You don't need to enable billing — everything we do is in the free tier.

### 3.2 Create a project

1. Click the **project picker** at the top-left of the page (it says the name of your current project, or "Select a project").
2. In the dialog that opens, click **NEW PROJECT** (top-right).
3. **Project name:** type `seo-data` (or anything you like — this name only shows in your console).
4. **Location:** leave as "No organization" unless you specifically need a Workspace organization.
5. Click **CREATE**.
6. Wait ~10 seconds for the project to be created. The page may not auto-switch — go back to the project picker and select your new project.

### 3.3 Enable the two APIs

You need to enable both the Search Console API and the Analytics Data API on this project.

1. In the left sidebar, click **APIs & Services → Library**.
   (If you don't see the sidebar, click the hamburger menu ☰ in the top-left.)
2. In the search bar at the top, type **`Google Search Console API`** and press Enter.
3. Click the result, then click **ENABLE**. Wait for it to activate.
4. Click the back arrow, then search for **`Google Analytics Data API`**.
5. Click the result, then click **ENABLE**.
6. (Optional but recommended) Search for **`Google Analytics Admin API`** and enable that too — it's used to list the GA4 properties you have access to.

### 3.4 Configure the OAuth consent screen

This is the screen users (you) see when they grant access.

1. Left sidebar: **APIs & Services → OAuth consent screen**.
2. **User Type:**
   - If you're using a personal Gmail account, you must pick **External**. (Internal is greyed out unless you have a Google Workspace.)
   - If you have a Google Workspace and you only intend to use this skill yourself, **Internal** is cleaner (no test-user limit, no warnings). Otherwise, **External** is fine.
3. Click **CREATE**.
4. **App name:** type `seo-data` (only shown to you during consent).
5. **User support email:** pick your own email.
6. **Developer contact email:** type your email again.
7. Leave everything else blank. Click **SAVE AND CONTINUE**.
8. **Scopes step:** click **SAVE AND CONTINUE** without adding anything. (We request scopes from the script, not the consent screen.)
9. **Test users step (only if you picked External):** click **+ ADD USERS** and add the Google email you'll connect with. Click **SAVE AND CONTINUE**.
10. Click **BACK TO DASHBOARD**.

The app stays in **Testing** mode forever. That's fine — Testing mode supports up to 100 listed test users without verification, which is more than enough for personal use.

### 3.5 Create the OAuth client

1. Left sidebar: **APIs & Services → Credentials**.
2. Click **+ CREATE CREDENTIALS** at the top, then **OAuth client ID**.
3. **Application type:** select **Desktop app**.
4. **Name:** type `seo-data desktop` (only shown to you).
5. Click **CREATE**.
6. A dialog appears with your client ID and secret. Click **DOWNLOAD JSON**.
7. The file downloads to your Downloads folder with a long name like `client_secret_1234...apps.googleusercontent.com.json`.

### 3.6 Move the JSON to the right place

The skill reads the OAuth client config from `~/.seo-data/google_client.json`. Create that directory and move the file there with that exact name.

**Windows (PowerShell):**

```powershell
# Create the directory if it doesn't exist
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.seo-data" | Out-Null

# Move and rename — adjust the source path to match your downloaded filename
Move-Item -Force "$env:USERPROFILE\Downloads\client_secret_*.json" "$env:USERPROFILE\.seo-data\google_client.json"
```

**macOS / Linux:**

```bash
mkdir -p ~/.seo-data
mv ~/Downloads/client_secret_*.json ~/.seo-data/google_client.json
```

If you saved the download somewhere else, replace `~/Downloads/...` with the actual path.

### 3.7 Run the connect script

**Windows:**

```powershell
python "$env:USERPROFILE\.claude\skills\seo-data\scripts\connect_google.py"
```

**macOS / Linux:**

```bash
python ~/.claude/skills/seo-data/scripts/connect_google.py
```

What happens next:

1. The script prints `Opening your browser for Google consent...`
2. Your default browser opens to a Google sign-in page.
3. **If you picked External + Testing mode**, you'll see a screen that says *"Google hasn't verified this app."* This is expected. Click **Advanced**, then **Go to seo-data (unsafe)**. (It's safe — you literally just created the app yourself in your own Google project. Google labels every Testing-mode app this way.)
4. Choose the Google account that has access to your GSC and GA4 properties.
5. Grant the read-only permissions to Search Console and Analytics.
6. The browser shows "Authentication complete. You can close this tab."
7. Back in your terminal, the script prints a JSON response listing every GSC site and GA4 property your account has access to.

If you get stuck at any step, see the [Troubleshooting](#troubleshooting) section.

---

## Part 4 — Pick a property

If your account had only one GSC site and one GA4 property and one verified Bing site, the skill auto-selected each one and you can skip this part. Otherwise:

### 4.1 List what's available

Run these to see your options:

```bash
python ~/.claude/skills/seo-data/scripts/set_property.py --provider gsc
python ~/.claude/skills/seo-data/scripts/set_property.py --provider ga4
python ~/.claude/skills/seo-data/scripts/set_property.py --provider bing
```

(Use the Windows-style path on PowerShell.)

### 4.2 Pick one

For GSC, use the full `siteUrl` you saw in the list. There are usually two formats:

- `sc-domain:example.com` — *domain property*, recommended. Captures all subdomains, www/non-www, and http/https in one report.
- `https://example.com/` — *URL prefix property*, only matches that exact origin.

```bash
# GSC — pick by site URL
python ~/.claude/skills/seo-data/scripts/set_property.py --provider gsc --site "sc-domain:example.com"

# GA4 — pick by property ID (the long number)
python ~/.claude/skills/seo-data/scripts/set_property.py --provider ga4 --property 123456789

# Bing — pick by site URL
python ~/.claude/skills/seo-data/scripts/set_property.py --provider bing --site "https://example.com/"
```

### 4.3 Verify everything is ready

```bash
python ~/.claude/skills/seo-data/scripts/status.py
```

You want to see `"ready": true` for each provider you connected.

---

## Part 5 — Verify in Claude

1. Open Claude Code (or restart it if it was already open — skills are loaded at startup).
2. Start a new conversation.
3. Ask something specific to your data, like:

   > "What were our top organic search queries last week, and which pages got the most traffic?"

4. Claude should:
   - Detect that this is an SEO question and trigger the `seo-data` skill
   - Run `status.py` to see what's connected
   - Call `gsc_query.py` for the queries half and `ga4_query.py` for the traffic half
   - Present the results with real SEO insight

If Claude answers generically without running scripts, the skill description in [SKILL.md](../SKILL.md) might need a tweak — open an issue or PR.

---

## Troubleshooting

### Install issues

**`pip: command not found`** — Python isn't on your PATH. Use `python -m pip` instead.

**`Could not find a version that satisfies the requirement google-analytics-data`** — your `pip` is too old. Run `python -m pip install --upgrade pip` first.

**`xcopy is not recognized` (Windows)** — you're in a Unix-style shell on Windows (Git Bash, WSL). Use the macOS/Linux instructions instead.

### Bing connection issues

**`Bing rejected the API key (401/403)`** — the key is wrong, expired, or revoked. Regenerate it from bing.com/webmasters → Settings → API Access.

**`No verified sites on this Bing account`** — verify a site in BWT first, then re-run the connect script.

**`No data found` when running queries** — the site is connected but has no recent data. Try increasing `--days` to a wider window, or check directly in BWT that the site has activity.

### Google connection issues

**`Access blocked: This app's request is invalid`** — you didn't enable both APIs (Search Console + Analytics Data). Go back to step 3.3.

**`Error 403: access_denied`** — you're signed in to a Google account that isn't listed as a test user. Either add that account in the OAuth consent screen → Test users, or sign in with the account you already added.

**`The OAuth client was not found`** — `google_client.json` is missing or corrupted. Re-download from APIs & Services → Credentials.

**Browser opens but the loopback redirect never completes** — a firewall is blocking `localhost`. Disable the firewall briefly or run on another machine.

**`invalid_grant` after the access token expires** — the refresh token was revoked or the OAuth client rotated. Run:

```bash
python ~/.claude/skills/seo-data/scripts/disconnect.py google
python ~/.claude/skills/seo-data/scripts/connect_google.py
```

**Want to use a different Google account** — same fix:

```bash
python ~/.claude/skills/seo-data/scripts/disconnect.py google
python ~/.claude/skills/seo-data/scripts/connect_google.py
# pick the new account in the browser
```

### Skill activation issues in Claude

**Claude doesn't trigger the skill on SEO questions** — make sure the skill is actually installed at `~/.claude/skills/seo-data/`. Check that `SKILL.md` is at the root of that folder (not nested deeper). Restart Claude Code.

**Claude triggers but uses the wrong provider** — the SKILL.md vocabulary mapping might need tightening for your phrasing. The lever is the `description:` line in the frontmatter and the "Vocabulary mapping" section in the body.

**Two skills both fire on the same question** — you have an older skill installed (e.g. `google-search-console`) that competes. Delete the old skill folder from `~/.claude/skills/`.

### Where credentials live

All under `~/.seo-data/` (Linux/macOS) or `%USERPROFILE%\.seo-data\` (Windows):

- `google_client.json` — your OAuth client (you provided this in step 3.6)
- `config.json` — refresh tokens, API keys, selected properties

To wipe everything and start over: delete the `.seo-data` directory.

---

That's it. Open a new Claude conversation and ask about your data.
