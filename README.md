# Dragnet

Dragnet is a keyword-driven internship posting monitor for a US-based engineering student. It sweeps free job board APIs twice a day, filters and scores the results against a keyword and location profile, dedupes them against prior runs, and delivers a markdown brief and an email digest.

```
INFO dragnet.adapters.usajobs: adapter=usajobs status=ok count=180
INFO dragnet.adapters.adzuna: adapter=adzuna status=ok count=72
INFO dragnet: new=14 seen=238
INFO dragnet: wrote brief: dragnet-briefs/2026-05-23.md
```

## Features

- Fans out across seven free job board APIs at once: USAJobs, Adzuna, JSearch, Remotive, Arbeitnow, RemoteOK, and HN's "Who is Hiring" thread.
- Filters postings by keyword category and internship signal, then scores them on location, recency, category match, and citizenship or clearance bonus.
- Dedupes postings with a fingerprint, so a rerun reports only what changed since the last one.
- Tracks each posting's lifecycle. A posting that a source stops returning for several runs in a row gets marked inactive.
- Extracts skills from posting text with a rule-based matcher, with a labeled evaluation set for precision and recall.
- Writes a daily markdown brief and sends an HTML email digest by Gmail SMTP.
- Runs on a schedule with macOS launchd, twice a day, with no server process to manage.

## Tech stack

- Python 3.12+
- httpx for the async adapter fan-out
- pydantic for the posting model and validation
- SQLite (stdlib `sqlite3`) for the seen-postings store, posting lifecycle, and skills tables
- jinja2 for the brief and email templates
- pyyaml and python-dotenv for config and secrets
- stdlib `smtplib` for the Gmail SMTP send
- macOS launchd for scheduling

## Prerequisites

- macOS 14 or later on Apple Silicon. The launchd plist and install script assume this platform.
- Python 3.12 or later.
- A Gmail account with 2FA enabled, for the digest sender.
- Free-tier API credentials for USAJobs, Adzuna, and JSearch (RapidAPI). See `docs/SETUP.md` for the registration steps.
- An Obsidian vault, if the markdown brief should land there. Set `notify.obsidian_brief_dir` in `config.yaml` and the vault path in `src/dragnet/config.py`.

## Quick start

```bash
git clone https://github.com/salshwauva/dragnet.git
cd dragnet
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
cp config.yaml.example config.yaml
```

Fill in `.env` with the API and Gmail credentials from `docs/SETUP.md`, then run a smoke test:

```bash
python -m dragnet --smoke-test -v
```

## Configuration

Secrets live in `.env` (copied from `.env.example`, gitignored). Behavior lives in `config.yaml` (copied from `config.yaml.example`, also gitignored): sources to enable, keyword categories, filter thresholds, and scoring weights.

| Variable | Required | Purpose |
|---|---|---|
| `USAJOBS_AUTH_KEY` | Yes | Authorization key from the USAJobs API request form. |
| `USAJOBS_USER_AGENT_EMAIL` | Yes | The email registered with USAJobs. Sent as the User-Agent header. |
| `ADZUNA_APP_ID` | Yes | Adzuna app ID from the developer dashboard. |
| `ADZUNA_APP_KEY` | Yes | Adzuna app key from the developer dashboard. |
| `RAPIDAPI_KEY` | Yes | RapidAPI key, subscribed to the JSearch API. |
| `GMAIL_ADDRESS` | Yes | The Gmail address that sends the digest. |
| `GMAIL_APP_PASSWORD` | Yes | A 16-character app password generated for that Gmail account. |

Remotive, Arbeitnow, RemoteOK, and HN Hiring need no credentials.

## Usage

```bash
python -m dragnet --smoke-test -v
```

Expected result: the run fetches, filters, scores, and dedupes postings, writes the markdown brief, and skips the email send.

Common commands:

```bash
python -m dragnet -v            # full run: writes the brief and sends the email digest
python -m dragnet --dry-run -v  # fetch, filter, and score only; prints the top results, writes nothing
```

## Tests and checks

```bash
pytest
ruff check .
ruff format --check .
mypy
```

`tests/test_skills_eval.py` reports precision, recall, and F1 for the skills extractor against a hand-labeled fixture. It skips while the labeled set is empty.

## Project structure

```text
src/dragnet/
  adapters/    one module per source; fetch and normalize only, no filtering
  pipeline/    filter, score, dedupe, and skills extraction
  storage/     the SQLite store: seen postings, lifecycle, skills, run history
  notify/      brief and email digest rendering and sending
  cli.py       entry point: python -m dragnet
  config.py    loads config.yaml and .env into a Config object
tests/         pytest suite, including the skills evaluation fixture
docs/          setup guide, native-alert companion setup, and architecture decisions
scripts/       launchd install script and a first-run smoke test
```

## Architecture

Each source has one adapter under `src/dragnet/adapters/`, subclassing `Adapter` from `adapters/base.py`. An adapter fetches and normalizes postings into the shared `Posting` model; it does not filter or score. The orchestrator in `pipeline/orchestrator.py` runs every adapter concurrently with `asyncio.gather`, bounded by `adapters.concurrent_limit`.

All filtering and scoring happens in `pipeline/`, after the fetch. A posting without a parseable start date is flagged, not dropped, and the score downranks it. Citizenship and clearance signals add to the score; they never gate a posting out.

Dedup and lifecycle state live in `storage/db.py`, the only module that touches the SQLite file directly. Each posting gets a fingerprint from its normalized fields, stable across whitespace and capitalization changes. A posting that a source stops returning for `lifecycle.inactive_after_misses` consecutive successful crawls of that source is marked inactive; only sources that returned without an error count toward that streak.

The design choices behind these pieces, and the reasoning for each, are recorded in `docs/decisions/` as one-page ADRs: public APIs only, the adapter fan-out pattern, the fingerprint dedup scheme, launchd over cron, soft start-date filtering, and citizenship as a scoring bonus.

## Deployment

The supported deployment is a single macOS machine running the process twice a day through launchd:

```bash
./scripts/install_launchd.sh
launchctl list | grep dragnet
```

The script fills in the repo path and symlinks the plist to `~/Library/LaunchAgents/`. Full setup, including the API registrations and the launchd install, is in `docs/SETUP.md`.

## Status

Active. The monitor runs twice a day. Posting lifecycle tracking and a rule-based skills extractor are in place. Skill extraction metrics wait on a larger labeled evaluation set; the current fixture is too small to report a reliable score.

## Contact

Open an issue on this repository.
