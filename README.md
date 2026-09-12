# Dragnet

Dragnet collects internship posts from job APIs and produces a ranked Markdown brief. It keeps a local SQLite history and can send a Gmail digest.

Keywords, dates, and location weights control which posts reach the brief. Each run checks several sources and separates new posts from earlier results.

## What it does

- Fetches posts concurrently from eight source adapters, including USAJobs, Adzuna, JSearch, and The Muse.
- Normalizes posts into a shared Pydantic model, then applies internship filters and a weighted score.
- Uses fingerprints to identify posts that appeared in earlier runs.
- Records first and last observations and marks posts inactive after repeated absences from a successful source fetch.
- Writes a Markdown brief and optionally sends an HTML email digest.

A failed source fetch does not count as a post's absence. The recorded dates describe Dragnet's observations, not an employer's open and close dates.

## Status

The default branch contains the monitor and posting lifecycle history. Skills extraction lives on a separate feature branch. The analytics API and dashboard are planned.

## Local setup

The supported environment is macOS 14 or later on Apple Silicon, with Python 3.12 or later.

```sh
git clone https://github.com/salshwauva/dragnet.git
cd dragnet
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
cp .env.example .env
cp config.yaml.example config.yaml
```

Credentials belong in `.env`. USAJobs, Adzuna, and JSearch require provider credentials. Gmail requires an app password for email delivery.

In `config.yaml`, set `paths.vault_root` to the folder that will receive briefs. The folder can be an Obsidian vault. Set unwanted sources to `false`, then adjust the search categories and date filters.

The example contains a dated internship search. Its dates and location weights need review before the first run.

## Run

Fetch posts and write a brief without an email:

```sh
python -m dragnet --smoke-test -v
```

This mode updates the database. A repeat run can produce fewer new posts because Dragnet remembers the first run.

Preview results without a brief or email:

```sh
python -m dragnet --dry-run
```

A normal run permits email delivery when `notify.email_enabled` is true and Gmail credentials are set:

```sh
python -m dragnet --once
```

The optional macOS schedule runs at 07:30 and 17:30 local time:

```sh
./scripts/install_launchd.sh
```

## Tests

```sh
python -m pytest -q
ruff check .
```

The tests cover models, filters, scores, duplicate detection, and posting lifecycle behavior. They use local test data.

## Source map

| Path | Purpose |
| --- | --- |
| `src/dragnet/adapters/` | Source APIs and normalization |
| `src/dragnet/pipeline/` | Concurrent fetches, filters, scores, and duplicate detection |
| `src/dragnet/storage/` | SQLite records and posting lifecycle |
| `src/dragnet/notify/` | Markdown and email output |
| `tests/` | Automated checks |

## Limits

Coverage depends on each source's access and returned results. A score measures configured preferences; it does not estimate the chance of an interview.

Source APIs can omit posts or change their quotas. Missing date information can remain in the brief with a flag. Native job alerts remain useful for sources outside this monitor.
