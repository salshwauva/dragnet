"""CLI entrypoint. `python -m dragnet [--smoke-test|--once|--dry-run]`."""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from pathlib import Path

from dragnet.config import Config, load_config
from dragnet.models import AdapterQuery
from dragnet.notify import send_email_digest, write_brief
from dragnet.pipeline.dedupe import split_new
from dragnet.pipeline.filters import annotate_and_filter
from dragnet.pipeline.orchestrator import fetch_all
from dragnet.pipeline.score import score_all
from dragnet.storage import SeenStore

log = logging.getLogger("dragnet")


def _configure_logging(cfg: Config, verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    fmt = "%(asctime)s %(levelname)s %(name)s: %(message)s"
    handlers: list[logging.Handler] = [logging.StreamHandler(sys.stdout)]
    log_path = Path(cfg.paths.log_path)
    if not log_path.is_absolute():
        log_path = cfg.repo_root / log_path
    handlers.append(logging.FileHandler(log_path))
    logging.basicConfig(level=level, format=fmt, handlers=handlers, force=True)


def _build_query(cfg: Config) -> AdapterQuery:
    """Flatten all category keywords into one OR'd query for the adapters."""
    flat: list[str] = []
    for kws in cfg.categories.values():
        flat.extend(kws)
    # Deduplicate while preserving order.
    seen: set[str] = set()
    unique = [k for k in flat if not (k in seen or seen.add(k))]
    return AdapterQuery(keywords=unique, intern_only=cfg.filters.intern_required)


async def _run_once(cfg: Config, *, dry_run: bool, smoke: bool) -> int:
    query = _build_query(cfg)
    raw = await fetch_all(cfg, query)
    log.info("fetched %d raw postings", len(raw))

    survivors = annotate_and_filter(raw, cfg)
    log.info("after filter: %d survivors", len(survivors))

    scored = score_all(survivors, cfg)

    db_path = Path(cfg.paths.db_path)
    if not db_path.is_absolute():
        db_path = cfg.repo_root / db_path
    store = SeenStore(db_path)
    try:
        new, seen = split_new(scored, store)
        log.info("new=%d seen=%d", len(new), len(seen))

        if dry_run:
            print(f"DRY RUN — would write brief with {len(new)} new postings.")
            for p in new[:10]:
                print(f"  [{p.score:>5.1f}] {p.source:>10}  {p.company} — {p.title}")
            return 0

        # Always persist all postings (new and seen — seen refreshes last_seen).
        store.upsert_many(scored)
        store.record_run(total=len(scored), new_count=len(new))

        # Write the brief. Always — even an empty brief is informative.
        brief_path = write_brief(new, cfg)
        if brief_path:
            print(f"wrote brief: {brief_path}")

        # Email only when there's something to report, and not in smoke mode.
        if not smoke:
            send_email_digest(new, cfg)
        else:
            log.info("smoke-test: skipping email send")
    finally:
        store.close()
    return 0


def main() -> None:
    ap = argparse.ArgumentParser(prog="dragnet", description="Internship monitor.")
    ap.add_argument(
        "--smoke-test",
        action="store_true",
        help="Run once, write brief, skip email. Use for first-run verification.",
    )
    ap.add_argument(
        "--once",
        action="store_true",
        help="Run once and exit (default; the launchd plist calls this).",
    )
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="Fetch + filter + score but don't write the brief or send email.",
    )
    ap.add_argument("-v", "--verbose", action="store_true", help="Debug logging.")
    args = ap.parse_args()

    cfg = load_config()
    _configure_logging(cfg, args.verbose)
    log.info("dragnet starting; vault=%s repo=%s", cfg.vault_root, cfg.repo_root)

    rc = asyncio.run(_run_once(cfg, dry_run=args.dry_run, smoke=args.smoke_test))
    sys.exit(rc)
