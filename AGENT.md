# AGENT.md — Runbook for AI Coding Agents

> **You are reading the agent runbook for the [seo-data](README.md) Claude Skill.**
> If you are a human reading this, follow [docs/SETUP.md](docs/SETUP.md) instead — it's written for you.

You are an AI agent (Claude Code, Cursor, Cline, Aider, etc.) installed in a clone of this repo. The user has asked you to set up the `seo-data` skill on their machine. This document is your runbook. Execute it phase by phase. Do not skip ahead. Do not improvise around the human-only steps.

The skill connects three providers:

- **Google Search Console** (OAuth) — search performance on Google
- **Google Analytics 4** (OAuth, same Google account) — on-site behavior
- **Bing Webmaster Tools** (API key) — search performance on Bing

The user may want one, two, or all three. Connect what they want; tell them they can come back later for the others.

---

## How to use this document

The runbook is split into phases. Each step is tagged so you know whether you act or the user acts:

- **`[AGENT]`** — you do this automatically. Run the command, parse the result, move on.
- **`[ASK USER]`** — pause and ask the user a specific question, then act on their answer.
- **`[TELL USER]`** — display literal instructions to the user (usually browser steps in Google Cloud Console or Bing Webmaster). Wait for them to confirm completion before continuing.
- **`[VERIFY]`** — run a check and decide whether to continue or surface an error.

When you `[TELL USER]` something, copy the instructions into your own response so they appear in the conversation. Do not paraphrase — these are exact UI labels.

---

## Phase 0 — Confirm the environment

### 0.1 [AGENT] Detect platform

Detect whether the user is on Windows, macOS, or Linux. You'll need this for path conventions throughout.

| Platform | Home directory | Path style |
|---|---|---|
| Windows | `%USERPROFILE%` (`C:\Users\<name>`) | backslash, `xcopy`, `PowerShell` |
| macOS / Linux | `~` (`/Users/<name>` or `/home/<name>`) | forward slash, `cp -r`, `bash` |

### 0.2 [AGENT] Confirm Python 3.10+

Run `python --version` (or `python3 --version` on Linux/macOS). If the version is below 3.10, `[TELL USER]`:

> Your Python version is too old. Please install Python 3.10 or newer from https://www.python.org/downloads/ and re-run me.

Then stop. Do not continue.

### 0.3 [AGENT] Confirm the Claude skills directory exists

Check whether `~/.claude/skills/` exists. If it does not, `[TELL USER]`:

> I can't find your Claude Code skills directory at `~/.claude/skills/`. Make sure Claude Code (or another agent that supports Claude Skills) is installed first: https://claude.com/claude-code

Then stop.

### 0.4 [AGENT] Check whether the skill is already installed

If `~/.claude/skills/seo-data/SKILL.md` already exists, `[ASK USER]`:

> The skill is already installed at `~/.claude/skills/seo-data/`. Do you want to (a) reinstall (overwrite), (b) reconfigure credentials only, or (c) skip and continue with another provider?

Branch based on their answer.

---

## Phase 1 — Install

### 1.1 [AGENT] Install Python dependencies

Run from the repo root:

```bash
pip install -r requirements.txt
```

If it fails with "permission denied," retry with `pip install --user -r requirements.txt`. If `pip` is not found, retry with `python -m pip install -r requirements.txt`.

`[VERIFY]` the install succeeded by checking that `google-api-python-client`, `google-auth-oauthlib`, `google-analytics-data`, and `requests` are listed in `pip list` output.

### 1.2 [AGENT] Copy the skill into the Claude skills directory

**Windows (PowerShell):**

```powershell
xcopy /E /I /Y . "$env:USERPROFILE\.claude\skills\seo-data"
```

**macOS / Linux:**

```bash
cp -r . ~/.claude/skills/seo-data
```

If you're running this from outside the cloned repo for some reason, use the full repo path instead of `.`.

### 1.3 [VERIFY] The install worked

Run:

```bash
python ~/.claude/skills/seo-data/scripts/status.py
```

(Or the Windows-style path with `$env:USERPROFILE`.)

You should get JSON with all `connected: false` and `ready: false`. If you get an error, surface the full stack trace to the user — do not continue.

---

## Phase 2 — Ask which providers to connect

### 2.1 [ASK USER] Which providers?

Ask the user, presenting these options:

> Which providers do you want to connect?
> 1. **Bing only** — fastest, just an API key
> 2. **Google only** (covers GSC + GA4) — ~10 minutes, requires Google Cloud setup
> 3. **All three** — recommended for full SEO coverage
> 4. **Skip — I'll do this later**

Branch based on the answer:

- 1 → go to **Phase 3 (Bing)**
- 2 → go to **Phase 4 (Google)**
- 3 → do **Phase 3 (Bing)** first because it's faster, then **Phase 4 (Google)**
- 4 → skip to **Phase 6 (Verify)**

You can re-enter Phase 3 or Phase 4 later if the user changes their mind.

---

## Phase 3 — Connect Bing Webmaster Tools

### 3.1 [TELL USER] Get the Bing API key

Show the user this exact instruction block:

> To connect Bing Webmaster Tools I need your API key. Here's how to get it:
>
> 1. Open https://www.bing.com/webmasters in a new browser tab.
> 2. Sign in with the Microsoft account that owns your Bing Webmaster Tools setup.
> 3. Click the gear icon (Settings) at the top-right.
> 4. Click **API Access** in the left sidebar.
> 5. Copy the API key shown there.
>
> Paste the key in your reply when you have it. (I'll never echo it back to you in a response.)

### 3.2 [ASK USER] Get the key

Wait for the user to paste their key.

When you receive it: **never repeat the key back in any of your text responses**. Treat it like a password.

### 3.3 [AGENT] Run the connect script

```bash
python ~/.claude/skills/seo-data/scripts/connect_bing.py --api-key <USER_KEY>
```

Capture the JSON output.

### 3.4 [AGENT] Handle the result

Possible outcomes:

- **Success with auto-selected site** (`auto_selected_site` in the output): `[TELL USER]` "Bing connected. Using site `<url>`." Move on.
- **Success with multiple sites** (`action_required` in the output): list the sites and `[ASK USER]` which one to use, then run:
  ```bash
  python ~/.claude/skills/seo-data/scripts/set_property.py --provider bing --site "<chosen url>"
  ```
- **`401`/`403` error**: tell the user the key was rejected and ask them to regenerate it from BWT. Loop back to step 3.1.
- **Network error**: tell the user there's a network problem and ask them to check their connection / firewall.
- **No verified sites**: tell the user their Bing account has no verified sites and they need to verify one in BWT first.

---

## Phase 4 — Connect Google (GSC + GA4)

This is the long one. The user has to do most of it in their browser; you handle file moves and command execution.

### 4.1 [TELL USER] Open Google Cloud Console

> To connect Google we need to create a free OAuth client in your own Google Cloud project. This takes about 5–10 minutes the first time. Don't worry about billing — everything is in the free tier.
>
> First step: open https://console.cloud.google.com/ in your browser and sign in with the Google account that owns your GSC sites and GA4 properties. Tell me when you're signed in.

Wait for confirmation.

### 4.2 [TELL USER] Create a project

> Now create a project:
>
> 1. Click the **project picker** at the top-left (it says the name of your current project, or "Select a project").
> 2. Click **NEW PROJECT** (top-right of the dialog).
> 3. **Project name:** `seo-data` (or any name you want).
> 4. **Location:** leave as "No organization" unless you have a specific Workspace org to use.
> 5. Click **CREATE** and wait ~10 seconds.
> 6. Switch into your new project via the project picker if it didn't auto-switch.
>
> Tell me when the project is created and selected.

Wait for confirmation.

### 4.3 [TELL USER] Enable the APIs

> Now enable two APIs:
>
> 1. In the left sidebar, click **APIs & Services → Library**.
> 2. Search for `Google Search Console API`, click the result, click **ENABLE**.
> 3. Click the back arrow, search for `Google Analytics Data API`, click the result, click **ENABLE**.
> 4. (Recommended) Search for `Google Analytics Admin API` and enable that too. It's used to list which GA4 properties your account has access to.
>
> Tell me when both APIs are enabled.

Wait for confirmation.

### 4.4 [TELL USER] Configure the OAuth consent screen

> Now configure the consent screen:
>
> 1. Left sidebar: **APIs & Services → OAuth consent screen**.
> 2. **User Type:**
>    - If you have a Google Workspace and only intend to use this skill yourself, pick **Internal**.
>    - Otherwise (personal Gmail, or you might want others to use it), pick **External**.
> 3. Click **CREATE**.
> 4. **App name:** `seo-data`
> 5. **User support email:** your email
> 6. **Developer contact email:** your email again
> 7. Click **SAVE AND CONTINUE** through every step. Don't add scopes manually.
> 8. **If you picked External:** on the "Test users" step, click **+ ADD USERS** and add the email you'll connect with.
> 9. Click **BACK TO DASHBOARD**.
>
> The app stays in **Testing** mode forever. You'll see an "unverified app" warning during consent — that's expected for Testing mode.
>
> Tell me when this is done.

Wait for confirmation.

### 4.5 [TELL USER] Create the OAuth client and download the JSON

> Now create the OAuth client:
>
> 1. Left sidebar: **APIs & Services → Credentials**.
> 2. Click **+ CREATE CREDENTIALS** → **OAuth client ID**.
> 3. **Application type:** **Desktop app**.
> 4. **Name:** `seo-data desktop`
> 5. Click **CREATE**.
> 6. Click **DOWNLOAD JSON** in the dialog that appears.
>
> The file downloads with a name like `client_secret_1234...apps.googleusercontent.com.json`. Note where it ended up (probably your Downloads folder).
>
> When the file is downloaded, tell me the full path to it.

### 4.6 [ASK USER] Get the file path

Wait for the user to paste the path. Common defaults:

- Windows: `C:\Users\<name>\Downloads\client_secret_<long-id>.json`
- macOS: `/Users/<name>/Downloads/client_secret_<long-id>.json`
- Linux: `/home/<name>/Downloads/client_secret_<long-id>.json`

If they paste a path with spaces or special characters, quote it properly when you use it.

### 4.7 [AGENT] Move the JSON to the right place

You handle this — don't make the user do file plumbing.

```bash
# Create the directory if it doesn't exist
mkdir -p ~/.seo-data        # Linux/macOS
# or
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.seo-data" | Out-Null   # Windows

# Move and rename
mv "<USER_PATH>" ~/.seo-data/google_client.json     # Linux/macOS
# or
Move-Item -Force "<USER_PATH>" "$env:USERPROFILE\.seo-data\google_client.json"   # Windows
```

`[VERIFY]` the file landed: check that `~/.seo-data/google_client.json` exists and is non-empty.

### 4.8 [AGENT + USER] Run the connect script

```bash
python ~/.claude/skills/seo-data/scripts/connect_google.py
```

The script will print "Opening your browser for Google consent..." and then block waiting for the user to complete consent.

`[TELL USER]`:

> Your browser should be opening now. Here's what to expect:
>
> 1. Sign in with the Google account that owns your GSC and GA4 properties.
> 2. **You'll see a "Google hasn't verified this app" warning.** This is expected because the app is in Testing mode. Click **Advanced**, then **Go to seo-data (unsafe)**. It is safe — you literally just created the app yourself in your own Google project.
> 3. Grant the read-only permissions to Search Console and Analytics.
> 4. The browser will show "Authentication complete. You can close this tab."
>
> When the browser confirms success, come back here.

When the script returns, parse the JSON output to see what the user has access to:

- `gsc_sites` — list of available Search Console sites
- `ga4_properties` — list of available GA4 properties
- `auto_selected` — what was auto-selected (if there was only one of each)
- `gsc_action_required` / `ga4_action_required` — present if the user needs to choose

### 4.9 [ASK USER + AGENT] Pick GSC site

If only one site exists, it's auto-selected and you skip this step.

Otherwise, present the list to the user:

> You have access to multiple GSC sites. Which one do you want to query?
>
> 1. `sc-domain:example.com` (siteOwner)
> 2. `https://example.com/` (siteOwner)
> 3. ...
>
> Tip: domain properties (`sc-domain:`) capture all subdomains and www/non-www variants in one report. URL prefix properties (`https://...`) only match that exact origin.

Then run:

```bash
python ~/.claude/skills/seo-data/scripts/set_property.py --provider gsc --site "<chosen siteUrl>"
```

### 4.10 [ASK USER + AGENT] Pick GA4 property

If only one property exists, it's auto-selected.

Otherwise:

> You have access to multiple GA4 properties. Which one?
>
> 1. `123456789` — Main Site (Personal Account)
> 2. `987654321` — Client Site (Client Account Name)
> 3. ...

Then:

```bash
python ~/.claude/skills/seo-data/scripts/set_property.py --provider ga4 --property <chosen property_id>
```

---

## Phase 5 — (Optional) Skipping?

If the user picked "Skip — I'll do this later" in Phase 2, just tell them how to come back:

> No problem. When you're ready to connect a provider, run me again with the same instruction, or use the manual steps in `docs/SETUP.md`.

---

## Phase 6 — Verify everything

### 6.1 [AGENT] Run status.py

```bash
python ~/.claude/skills/seo-data/scripts/status.py
```

`[VERIFY]` that for every provider the user wanted to connect, `connected: true` and `ready: true`.

### 6.2 [AGENT] Run a smoke query against each connected provider

For each `ready: true` provider, run a small query:

- **GSC:** `python ~/.claude/skills/seo-data/scripts/gsc_query.py --report queries --days 30 --limit 5`
- **GA4:** `python ~/.claude/skills/seo-data/scripts/ga4_query.py --report overview --days 30`
- **Bing:** `python ~/.claude/skills/seo-data/scripts/bing_query.py --report traffic --days 30`

If any query errors out, surface the error to the user. Don't pretend it worked.

### 6.3 [TELL USER] You're done

> Setup complete. Here's what's connected:
>
> - GSC: <site>
> - GA4: <property> (<display name>)
> - Bing: <site>
>
> Restart Claude Code so it picks up the skill, then ask any SEO question. For example:
>
>   *"What were our top organic search queries last week, and which pages got the most traffic?"*
>
> If you want to switch property, disconnect a provider, or reconnect a different account later, the commands are documented in [docs/SETUP.md](docs/SETUP.md) Part 4.

---

## Rules for the agent

These apply throughout. Treat them as hard constraints:

1. **Never echo API keys, refresh tokens, or OAuth secrets** in your text responses, even if the user pastes one. Use them in commands but don't repeat them in chat.
2. **Use absolute paths** in shell commands (`~/.claude/skills/seo-data/...`, `$env:USERPROFILE\.claude\skills\seo-data\...`). Don't rely on the user's current working directory.
3. **Verify every phase before moving on.** Run `status.py` between phases. If something failed, stop and surface the error rather than pressing forward.
4. **Don't paraphrase the [TELL USER] instruction blocks.** The Google Cloud Console UI labels are exact. If you change "**Application type:** **Desktop app**" to "select desktop application," the user's UI won't match what they see.
5. **Stop if Python or Claude Code is missing.** These are hard prerequisites — there's no point continuing.
6. **If a step fails twice the same way**, stop and ask the user for help. Don't loop on the same error.
7. **The user can interrupt you at any time** to skip a phase or correct a wrong assumption. Re-read the instructions and pick up where they want.

## When to fall back to docs/SETUP.md

If anything in this runbook becomes ambiguous (e.g. Google Cloud Console UI changes, error messages you don't recognize), surface the issue to the user and point them at [docs/SETUP.md](docs/SETUP.md), which has the human-readable troubleshooting section. Don't guess.
