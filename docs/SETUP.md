# Setup

End-to-end install: ~45 minutes including the three free-tier API registrations.

## Prerequisites

- macOS 14+ on Apple Silicon (the launchd plist and scripts assume this).
- Python 3.12+ (`python3 --version` to check; if missing, install via `brew install python@3.12`).
- A Gmail account with **2FA enabled** (the digest sender; can be the same as your main account).
- Obsidian vault at `~/my-vault` or the iCloud vault path (autodetected; set `paths.vault_root` in `config.yaml` if elsewhere).

## 1. Register at the three free-tier API providers

### USAJobs (~5 min)
1. Go to https://developer.usajobs.gov/apirequest/
2. Click **Request Authorization Key**. Fill in your email + name + a short description ("personal internship monitor").
3. You'll receive an `Authorization-Key` by email. Save it; it goes in `.env` as `USAJOBS_AUTH_KEY`.
4. The email address you registered with is your `USAJOBS_USER_AGENT_EMAIL` — it's required as a User-Agent header on every request.

### Adzuna (~5 min)
1. Go to https://developer.adzuna.com/
2. **Sign Up** → confirm email.
3. Once logged in, dashboard shows your `app_id` and `app_key`. These are `ADZUNA_APP_ID` and `ADZUNA_APP_KEY` in `.env`.
4. Free tier: 1000 calls/month. Dragnet's default config uses ~14 calls/day, well under quota.

### RapidAPI JSearch (~5 min)
1. Go to https://rapidapi.com → sign up (Google/GitHub SSO works).
2. Browse to **JSearch** at https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch
3. Click **Subscribe to Test** → choose **Basic (Free)** plan: 200 calls/month.
4. In your dashboard, your `x-rapidapi-key` is at the top. That's `RAPIDAPI_KEY` in `.env`.
5. Dragnet's default config uses ~7 calls/day (one page per run, twice daily), well under the 200/month quota.

### Gmail App Password (~5 min)
1. Go to https://myaccount.google.com/security
2. Confirm **2-Step Verification** is on. If not, enable it now.
3. Go to https://myaccount.google.com/apppasswords
4. **Select app:** Mail → **Select device:** Other → name it "Dragnet" → **Generate**.
5. Save the 16-character password. That's `GMAIL_APP_PASSWORD` in `.env`. The address is `GMAIL_ADDRESS`.

## 2. Install

From the unpacked tarball directory:

```bash
./install.sh
```

The script:
1. Confirms your vault and code-root paths.
2. Copies vault notes to `<vault>/Tech/coding projects/dragnet/`.
3. Copies repo to `<code-root>/dragnet/`.
4. Creates `.venv`, installs dependencies via `pip install -e ".[dev]"`.
5. Initializes git.
6. Prints next steps.

## 3. Configure

```bash
cd ~/dragnet
cp .env.example .env
cp config.yaml.example config.yaml
```

Fill in `.env` with the 5 credential values from step 1.

Edit `config.yaml` if you want to change scoring weights or disable a source (the defaults are reasonable).

## 4. First run (smoke test)

```bash
source .venv/bin/activate
python -m dragnet --smoke-test -v
```

This fetches, filters, scores, dedupes, and writes the brief — but skips the email send. Watch the log for adapter status lines:

```
INFO dragnet.adapters.usajobs: adapter=usajobs status=ok count=180
INFO dragnet.adapters.adzuna: adapter=adzuna status=ok count=72
...
INFO dragnet: wrote brief: ~/vault/Tech/job-search/dragnet-briefs/2026-05-23.md
```

Open the brief in Obsidian. If you see postings, Layer 2 is working.

## 5. Second run (verify dedup)

```bash
python -m dragnet --smoke-test -v
```

The brief should now show `0 new postings` (or close to it — there may be 1-2 fresh hits between the two runs). Dedup is working.

## 6. Full run (enable email)

```bash
python -m dragnet -v
```

Check your Gmail. The digest should arrive within ~30 seconds.

## 7. Install the launchd schedule

```bash
./scripts/install_launchd.sh
```

The script substitutes your repo path into the plist template and symlinks it to `~/Library/LaunchAgents/`. Verify with:

```bash
launchctl list | grep dragnet
```

You should see `com.dragnet.scraper` listed. From now on, it runs at 7:30 AM and 5:30 PM local time without your intervention.

## 8. Gmail filters + Layer 1 alerts

See `GMAIL_FILTERS.md` and `LAYER1_NATIVE_ALERTS.md`. Do these in one Saturday-morning sitting if you can.

## Troubleshooting

**`401 Unauthorized` from USAJobs.** Double-check the `User-Agent` is the registered email, not your name.

**`429 Too Many Requests` from Adzuna or RapidAPI.** You've hit a quota. Check `dragnet.log` for the source. Lower `adzuna_pages` or `jsearch_pages` in `config.yaml`.

**No email arrives but no error in logs.** Check `notify.email_enabled: true` and that `notify.email_min_score` isn't filtering everything out (default 50 — lower if your first run has nothing above it).

**`vault_root not detected`.** Set `paths.vault_root` in `config.yaml` to your vault folder.

**launchd doesn't fire.** `launchctl list | grep dragnet` to confirm it's loaded. `tail -f dragnet.log dragnet.err` while waiting for the next scheduled run.
