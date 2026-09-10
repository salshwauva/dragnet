"""Rule-based skills extraction: boundaries, aliases, canonical dedup, storage."""

from pathlib import Path

from dragnet.models import Posting
from dragnet.pipeline.dedupe import fingerprint
from dragnet.pipeline.skills import canonicalize, extract, extract_all, match
from dragnet.pipeline.skills_vocab import VOCAB
from dragnet.storage import SeenStore


def _names(text: str) -> list[str]:
    return [s.name for s in extract(text)]


def test_symbol_languages_match_as_whole_tokens() -> None:
    assert _names("Experience in C/C++, C#, and .NET.") == [".NET", "C", "C#", "C++"]


def test_symbol_boundaries_reject_superstrings() -> None:
    assert match("c+++ and asp.nets and pythonic") == set()


def test_matching_is_case_insensitive() -> None:
    assert _names("PYTHON and Kubernetes") == ["Kubernetes", "Python"]


def test_aliases_collapse_to_one_canonical_skill() -> None:
    hits = match("k8s, Kubernetes, kubernetes")
    assert hits == {"k8s", "kubernetes"}
    assert [s.name for s in canonicalize(hits)] == ["Kubernetes"]


def test_common_english_words_do_not_match() -> None:
    assert _names("Go to the arm of the company and grab a spring coffee.") == []


def test_vocab_aliases_are_unique_across_skills() -> None:
    seen: set[str] = set()
    for skill in VOCAB:
        for alias in skill.aliases:
            assert alias not in seen, alias
            seen.add(alias)


def test_extract_all_uses_title_and_body_and_store_round_trips(tmp_path: Path) -> None:
    post = Posting(
        source="usajobs",
        source_id="1",
        url="https://x",
        title="Rust Intern",
        company="ACo",
        location="Boston, MA",
        description="Python and Rust. Docker a plus.",
    )
    fingerprint(post)
    store = SeenStore(tmp_path / "t.db")
    try:
        store.upsert_many([post])
        store.save_skills(extract_all([post]))
        assert store.skills_for(post.fingerprint) == ["Docker", "Python", "Rust"]
        # Rerun with a smaller set replaces, never accumulates.
        store.save_skills({post.fingerprint: [("Rust", "language")]})
        assert store.skills_for(post.fingerprint) == ["Rust"]
    finally:
        store.close()
