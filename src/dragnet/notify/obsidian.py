"""Write the daily markdown brief into the Obsidian vault."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from dragnet.config import Config
from dragnet.models import Posting

log = logging.getLogger(__name__)


def _render(postings: list[Posting], cfg: Config) -> str:
    tpl_dir = Path(__file__).parent / "templates"
    env = Environment(
        loader=FileSystemLoader(str(tpl_dir)),
        autoescape=select_autoescape(["html"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    tpl = env.get_template("brief.md.j2")
    return tpl.render(
        postings=postings,
        today=datetime.now().strftime("%Y-%m-%d"),
        total=len(postings),
    )


def write_brief(postings: list[Posting], cfg: Config) -> Path | None:
    """Write the brief into the vault. Returns the file path, or None if vault not found.

    Filename: `<YYYY-MM-DD>.md`. If a brief already exists for today, it's overwritten —
    intentional, because re-runs on the same day should refresh, not pile up.
    """
    if not cfg.vault_root:
        log.warning("vault_root not detected; skipping markdown brief")
        return None
    out_dir = cfg.vault_root / cfg.notify.obsidian_brief_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{datetime.now().strftime('%Y-%m-%d')}.md"
    body = _render(postings, cfg)
    out_path.write_text(body, encoding="utf-8")
    log.info("wrote brief: %s (%d postings)", out_path, len(postings))
    return out_path
