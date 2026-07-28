"""Scoring. Composite = location + recency + categories + citizenship/clearance bonuses."""

from __future__ import annotations

import re
from datetime import UTC, datetime

from dragnet.config import Config
from dragnet.models import Posting

# Substring matchers for location buckets. Order matters — first hit wins.
# Patterns are (regex, bucket_name).
_LOCATION_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    # remote/hybrid handled separately via flags
    (
        re.compile(
            r"\b(boston|cambridge|somerville|waltham|burlington|"
            r"watertown|allston|brookline|natick|framingham|"
            r"milford|holliston|metrowest)\b",
            re.IGNORECASE,
        ),
        "boston",
    ),
    (
        re.compile(
            r"\b(washington,? d\.?c\.?|arlington|reston|fairfax|"
            r"bethesda|tysons|alexandria|chantilly|herndon|"
            r"mclean|silver spring)\b",
            re.IGNORECASE,
        ),
        "dc",
    ),
    (
        re.compile(
            r"\b(new york|nyc|brooklyn|manhattan|jersey city|"
            r"queens|bronx)\b",
            re.IGNORECASE,
        ),
        "nyc",
    ),
    (
        re.compile(
            r"\b(philadelphia|philly|conshohocken|king of prussia|"
            r"wayne, pa|west chester)\b",
            re.IGNORECASE,
        ),
        "philly",
    ),
    (re.compile(r"\b(chicago|evanston|naperville|schaumburg)\b", re.IGNORECASE), "chicago"),
]


def location_score(post: Posting, cfg: Config) -> float:
    """Return the location component. Highest match wins."""
    weights = cfg.score.location
    if post.is_remote:
        return weights.remote
    if post.is_hybrid:
        return weights.hybrid
    loc = post.location or ""
    for pattern, bucket in _LOCATION_PATTERNS:
        if pattern.search(loc):
            return getattr(weights, bucket)
    # Final fallback: assume US (most sources are US-only) unless explicit non-US.
    lower = loc.lower()
    non_us_markers = (
        "london",
        "berlin",
        "paris",
        "amsterdam",
        "dublin",
        "toronto",
        "vancouver",
        "bangalore",
        "tokyo",
        "singapore",
        "tel aviv",
        "remote (emea)",
        "remote (apac)",
        "uk",
        "germany",
    )
    if any(m in lower for m in non_us_markers):
        return weights.international
    return weights.other_us


def recency_score(post: Posting, cfg: Config) -> float:
    """Newer postings score higher. Floor at 0."""
    if not post.posted_at:
        return 0.0
    posted = post.posted_at
    if posted.tzinfo is None:
        posted = posted.replace(tzinfo=UTC)
    now = datetime.now(UTC)
    days = max(0, (now - posted).days)
    return max(0.0, 50 - days * cfg.score.recency_decay)


def category_score(post: Posting, cfg: Config) -> float:
    """Sum of base * weight across matched categories."""
    base = cfg.score.category_match
    total = 0.0
    for cat in post.matched_categories:
        w = cfg.category_weights.get(cat, 1.0)
        total += base * w
    return total


def fit_bonus(post: Posting, cfg: Config) -> float:
    """Citizenship / clearance bonus. Sophia's eligibility makes these an edge."""
    bonus = 0.0
    if post.requires_clearance:
        bonus += cfg.score.clearance_bonus
    if post.requires_citizenship:
        bonus += cfg.score.citizenship_bonus
    return bonus


def score_one(post: Posting, cfg: Config) -> float:
    """Compute composite score and assign it to post.score. Returns the score."""
    s = (
        location_score(post, cfg)
        + recency_score(post, cfg)
        + category_score(post, cfg)
        + fit_bonus(post, cfg)
    )
    post.score = round(s, 1)
    return post.score


def score_all(postings: list[Posting], cfg: Config) -> list[Posting]:
    """Score every posting; return sorted descending by score."""
    for p in postings:
        score_one(p, cfg)
    return sorted(postings, key=lambda p: p.score, reverse=True)
