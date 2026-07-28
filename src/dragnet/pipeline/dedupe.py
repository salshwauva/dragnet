"""Dedup. Computes a stable fingerprint per posting and separates new vs. seen.

The fingerprint is `sha1(source + normalized_company + normalized_title + normalized_location)`.
Normalization: lowercase, strip whitespace, collapse internal whitespace, drop punctuation.
This survives small reorderings and reposts with cosmetic changes while still
distinguishing real new postings.
"""

from __future__ import annotations

import hashlib
import re

from dragnet.models import Posting
from dragnet.storage.db import SeenStore

_WS_RE = re.compile(r"\s+")
_PUNCT_RE = re.compile(r"[^\w\s]")


def _normalize(s: str) -> str:
    s = (s or "").lower()
    s = _PUNCT_RE.sub("", s)
    s = _WS_RE.sub(" ", s).strip()
    return s


def fingerprint(post: Posting) -> str:
    """Stable hash for dedup. Sets post.fingerprint and returns it."""
    parts = [
        post.source,
        _normalize(post.company),
        _normalize(post.title),
        _normalize(post.location)[:80],  # cap to avoid huge "remote (50 states listed)" strings
    ]
    raw = "|".join(parts).encode("utf-8")
    fp = hashlib.sha1(raw, usedforsecurity=False).hexdigest()
    post.fingerprint = fp
    return fp


def split_new(postings: list[Posting], store: SeenStore) -> tuple[list[Posting], list[Posting]]:
    """Compute fingerprints, mark seen state. Return (new, already_seen)."""
    for p in postings:
        fingerprint(p)
    fps = [p.fingerprint for p in postings]
    seen_set = store.contains_many(fps)
    new: list[Posting] = []
    seen: list[Posting] = []
    for p in postings:
        if p.fingerprint in seen_set:
            seen.append(p)
        else:
            new.append(p)
    return new, seen
