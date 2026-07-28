# ADR 0004: launchd, not cron, for scheduling

## Status
Accepted — 2026-05-22

## Context
Dragnet runs twice daily on Sophia's MacBook. The laptop is closed and asleep through some scheduled runs (overnight especially). Cron on macOS doesn't handle missed runs gracefully and is not the recommended scheduler on the platform.

## Decision
Use macOS launchd. The plist lives at `~/Library/LaunchAgents/com.dragnet.scraper.plist` and is installed by `scripts/install_launchd.sh`. `StartCalendarInterval` schedules 07:30 and 17:30 local. Per-user LaunchAgent (not root), so no sudo. `RunAtLoad: false` so loading the plist doesn't fire it; manual runs use `python -m dragnet --once`.

## Consequences
Easier: launchd handles missed runs on wake, runs as user, native to the platform, plist is one file in version control.
Harder: launchd debugging is more obscure than cron. `launchctl` syntax is less famous. Future cross-platform support would mean rewriting this layer.

## Alternatives considered
- **cron.** Rejected for missed-run behavior on macOS.
- **GitHub Actions on a schedule.** Rejected: would mean putting all API keys in repo secrets, and the brief writes to a local Obsidian path. Complexity isn't worth it.
- **A long-running Python process with `schedule` or APScheduler.** Rejected: process management on a personal laptop is unnecessary friction.
