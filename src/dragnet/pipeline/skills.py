"""Rule-based skills extraction. Deterministic: vocabulary, alias regex, canonical dedup.

Two stages, kept separate so each can be tested and swapped on its own:
  match()        -> which alias strings occur in the text
  canonicalize() -> alias strings to unique Skill rows
"""

from __future__ import annotations

import re
from functools import cache

from dragnet.models import Posting
from dragnet.pipeline.skills_vocab import VOCAB, Skill

# \b treats "+", "#" and "." as non-word, so "c++" would match inside "c+++" and
# ".net" inside "asp.net". These boundaries also refuse those symbols.
_LEFT = r"(?<![\w+#])"
_RIGHT = r"(?![\w+#])"

# Canonical names are not implicit aliases: "Go", "ARM" and "Spring" are English words.
_ALIAS_TO_SKILL: dict[str, Skill] = {alias: skill for skill in VOCAB for alias in skill.aliases}


@cache
def _alias_regex(alias: str) -> re.Pattern[str]:
    return re.compile(_LEFT + re.escape(alias) + _RIGHT, re.IGNORECASE)


def match(text: str) -> set[str]:
    """Return every vocabulary alias that occurs as a whole token in `text`."""
    return {alias for alias in _ALIAS_TO_SKILL if _alias_regex(alias).search(text)}


def canonicalize(aliases: set[str]) -> list[Skill]:
    """Map alias hits to their canonical Skill, one row per skill, sorted by name."""
    return sorted({_ALIAS_TO_SKILL[a] for a in aliases}, key=lambda s: s.name)


def extract(text: str) -> list[Skill]:
    return canonicalize(match(text))


def extract_all(postings: list[Posting]) -> dict[str, list[tuple[str, str]]]:
    """Fingerprint -> (name, category) pairs, the shape the storage layer accepts."""
    return {
        p.fingerprint: [(s.name, s.category) for s in extract(f"{p.title}\n{p.description}")]
        for p in postings
    }
