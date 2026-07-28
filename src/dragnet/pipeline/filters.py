"""Filter chain. Each function MUTATES the Posting with computed flags + categories,
then the survivor predicate decides what to keep.

The filter chain follows the "flag, don't drop" rule for soft signals like start date.
Hard drops only happen for explicit non-fits (e.g. "Summer 2026 only" when configured).
"""

from __future__ import annotations

import re
from functools import cache

from dragnet.config import Config
from dragnet.models import Posting


@cache
def _kw_regex(kw: str) -> re.Pattern[str]:
    """Word-boundary matcher for a category keyword, compiled once and cached.

    Prevents substring false positives like the token "swe" matching inside the
    German word "Auswertungen". Phrases and punctuated keywords (e.g. "ts/sci",
    "full-stack") are escaped so only standalone occurrences match.
    """
    return re.compile(r"\b" + re.escape(kw) + r"\b", re.IGNORECASE)


# === Intern detection ===
# Title hits weight more than body hits because titles are intentional.
_INTERN_TITLE_RE = re.compile(
    r"\b(intern(ship)?|co-op|coop|trainee|apprentice|early career)\b", re.IGNORECASE
)
_INTERN_BODY_RE = re.compile(
    r"\b(intern(ship)?|co-op|coop|undergraduate students?|graduate students?|"
    r"current students?|enrolled in a (bachelor|master|degree))\b",
    re.IGNORECASE,
)
_INTERN_EXCLUDE_RE = re.compile(
    r"\b(internship coordinator|intern manager|intern program manager)\b", re.IGNORECASE
)

# === Citizenship / clearance ===
_CITIZENSHIP_RE = re.compile(
    r"\b(u\.?s\.? citizen|united states citizen|citizenship required|"
    r"must be a u\.?s\.? citizen)\b",
    re.IGNORECASE,
)
_CLEARANCE_RE = re.compile(
    r"\b(security clearance|secret clearance|top secret|ts/sci|"
    r"active clearance|polygraph|sci eligibility)\b",
    re.IGNORECASE,
)

# === Start date heuristics ===
# Months that line up with a Fall 2026 start.
_FALL_2026_RE = re.compile(
    r"\b(fall 2026|fall '26|fall ‘26|august 2026|aug 2026|september 2026|sep 2026|"
    r"sept 2026|october 2026|oct 2026|q4 2026|q3 2026)\b",
    re.IGNORECASE,
)
# Explicit non-fits.
_SUMMER_ONLY_RE = re.compile(
    r"\b(summer 2026 only|summer-only|summer-only internship|"
    r"this is a summer 2026 internship)\b",
    re.IGNORECASE,
)
_SPRING_ONLY_RE = re.compile(
    r"\b(spring 2026 only|this is a spring 2026 internship)\b", re.IGNORECASE
)

# === Remote / hybrid ===
_REMOTE_RE = re.compile(r"\b(remote|work from anywhere|fully remote|wfh)\b", re.IGNORECASE)
_HYBRID_RE = re.compile(r"\b(hybrid|partially remote|on-?site \d+ days?)\b", re.IGNORECASE)


def annotate(post: Posting, cfg: Config) -> None:
    """Annotate the posting in place with all computed flags + categories."""
    title = post.title or ""
    body = post.description or ""
    haystack = f"{title}\n{body}"

    # Intern signal: title hit = 1.0, body hit = 0.5, exclude knocks it to 0.
    if _INTERN_EXCLUDE_RE.search(title):
        post.intern_signal = 0.0
    elif _INTERN_TITLE_RE.search(title):
        post.intern_signal = 1.0
    elif _INTERN_BODY_RE.search(body):
        post.intern_signal = 0.5
    else:
        post.intern_signal = 0.0

    # Citizenship / clearance (don't overwrite if adapter already set them).
    if not post.requires_citizenship:
        post.requires_citizenship = bool(_CITIZENSHIP_RE.search(haystack))
    if not post.requires_clearance:
        post.requires_clearance = bool(_CLEARANCE_RE.search(haystack))

    # Start date confidence.
    if _SUMMER_ONLY_RE.search(haystack) or (
        cfg.filters.drop_spring_only and _SPRING_ONLY_RE.search(haystack)
    ):
        post.start_date_confidence = "non-fit"
    elif _FALL_2026_RE.search(haystack):
        post.start_date_confidence = "match"
        # extract the matched phrase for display
        m = _FALL_2026_RE.search(haystack)
        if m:
            post.start_date_raw = m.group(0)
    else:
        post.start_date_confidence = "unknown"

    # Remote / hybrid (don't overwrite an adapter that already knew).
    if not post.is_remote:
        loc_lower = (post.location or "").lower()
        post.is_remote = bool(_REMOTE_RE.search(haystack) or "remote" in loc_lower)
    if not post.is_hybrid and not post.is_remote:
        post.is_hybrid = bool(_HYBRID_RE.search(haystack))

    # Category matching. Word-boundary, not substring, to avoid false positives.
    matched: list[str] = []
    for cat, kws in cfg.categories.items():
        for kw in kws:
            if _kw_regex(kw).search(haystack):
                matched.append(cat)
                break
    post.matched_categories = matched


def keep(post: Posting, cfg: Config) -> bool:
    """Decide whether to keep this posting. Drops only on explicit non-fits."""
    if cfg.filters.intern_required and post.intern_signal < 0.5:
        return False
    # Two parallel guard clauses read clearer than one negated boolean.
    if cfg.filters.drop_summer_2026 and post.start_date_confidence == "non-fit":  # noqa: SIM103
        return False
    return True


def annotate_and_filter(postings: list[Posting], cfg: Config) -> list[Posting]:
    """Run the full chain. Return survivors in the same order."""
    survivors: list[Posting] = []
    for p in postings:
        annotate(p, cfg)
        if keep(p, cfg):
            survivors.append(p)
    return survivors
