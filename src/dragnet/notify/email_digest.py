"""Send the email digest via Gmail SMTP using an app password."""

from __future__ import annotations

import logging
import smtplib
from datetime import datetime
from email.message import EmailMessage
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from dragnet.config import Config
from dragnet.models import Posting

log = logging.getLogger(__name__)

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 465


def _render_both(postings: list[Posting], cfg: Config) -> tuple[str, str]:
    tpl_dir = Path(__file__).parent / "templates"
    env = Environment(
        loader=FileSystemLoader(str(tpl_dir)),
        autoescape=select_autoescape(["html"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    today = datetime.now().strftime("%Y-%m-%d")
    text = env.get_template("email.txt.j2").render(
        postings=postings, today=today, total=len(postings)
    )
    html = env.get_template("email.html.j2").render(
        postings=postings, today=today, total=len(postings)
    )
    return text, html


def send_email_digest(new_postings: list[Posting], cfg: Config) -> None:
    """Build and send the digest. No-op if email disabled or creds missing."""
    if not cfg.notify.email_enabled:
        log.info("email disabled in config")
        return
    if not (cfg.secrets.gmail_address and cfg.secrets.gmail_app_password):
        log.warning("Gmail creds missing; skipping email")
        return

    # Cap and threshold per config.
    candidates = [p for p in new_postings if p.score >= cfg.notify.email_min_score]
    candidates.sort(key=lambda p: p.score, reverse=True)
    capped = candidates[: cfg.notify.email_max_postings]
    if not capped:
        log.info("no postings meet email_min_score=%s; not sending", cfg.notify.email_min_score)
        return

    text, html = _render_both(capped, cfg)

    msg = EmailMessage()
    msg["From"] = cfg.notify.email_from or cfg.secrets.gmail_address
    msg["To"] = cfg.notify.email_to or cfg.secrets.gmail_address
    today = datetime.now().strftime("%Y-%m-%d")
    msg["Subject"] = f"[Dragnet] {len(capped)} new postings — {today}"
    msg.set_content(text)
    msg.add_alternative(html, subtype="html")

    try:
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as s:
            s.login(cfg.secrets.gmail_address, cfg.secrets.gmail_app_password)
            s.send_message(msg)
        log.info("sent digest to %s (%d postings)", msg["To"], len(capped))
    except (smtplib.SMTPException, OSError) as e:
        log.error("email send failed: %s", e)
