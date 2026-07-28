"""Notify: render and send. No filtering or scoring here."""

from dragnet.notify.email_digest import send_email_digest
from dragnet.notify.obsidian import write_brief

__all__ = ["write_brief", "send_email_digest"]
