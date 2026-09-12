"""Posting lifecycle: first/last seen, absence counting, inactive detection."""

from pathlib import Path
from typing import Any

import pytest

from dragnet.models import Posting
from dragnet.pipeline.dedupe import fingerprint
from dragnet.storage import SeenStore


def _p(source: str = "usajobs", title: str = "Software Intern", **kw) -> Posting:
    base: dict[str, Any] = dict(
        source=source,
        source_id="1",
        url="https://x",
        title=title,
        company="ACo",
        location="Boston, MA",
        description="Experience with Python.",
    )
    base.update(kw)
    post = Posting(**base)
    fingerprint(post)
    return post


@pytest.fixture
def store(tmp_path: Path):
    s = SeenStore(tmp_path / "t.db")
    yield s
    s.close()


def _crawl(store: SeenStore, postings: list[Posting], sources: set[str], threshold: int = 3) -> int:
    """One run as cli.py performs it: upsert what we saw, then age what we did not."""
    store.upsert_many(postings)
    return store.mark_absent({p.fingerprint for p in postings}, sources, threshold)


def test_new_posting_gets_timestamps_and_active_status(store: SeenStore):
    p = _p()
    _crawl(store, [p], {"usajobs"})
    rec = store.get(p.fingerprint)
    assert rec is not None
    assert rec.first_seen == rec.last_seen
    assert rec.status == "active"
    assert rec.closed_at is None
    assert rec.missed_runs == 0
    assert rec.full_text == "Experience with Python."


def test_repeated_ingestion_does_not_duplicate(store: SeenStore):
    p = _p()
    _crawl(store, [p], {"usajobs"})
    _crawl(store, [p], {"usajobs"})
    assert store.count() == 1


def test_existing_posting_updates_last_seen_keeps_first_seen(store: SeenStore):
    p = _p()
    _crawl(store, [p], {"usajobs"})
    before = store.get(p.fingerprint)
    assert before is not None
    _crawl(store, [p], {"usajobs"})
    after = store.get(p.fingerprint)
    assert after is not None
    assert after.first_seen == before.first_seen
    assert after.last_seen >= before.last_seen


def test_single_absence_does_not_close(store: SeenStore):
    p = _p()
    _crawl(store, [p], {"usajobs"})
    closed = _crawl(store, [], {"usajobs"})
    rec = store.get(p.fingerprint)
    assert closed == 0
    assert rec is not None
    assert rec.status == "active"
    assert rec.missed_runs == 1


def test_threshold_absences_mark_inactive(store: SeenStore):
    p = _p()
    _crawl(store, [p], {"usajobs"})
    assert _crawl(store, [], {"usajobs"}, threshold=3) == 0
    assert _crawl(store, [], {"usajobs"}, threshold=3) == 0
    assert _crawl(store, [], {"usajobs"}, threshold=3) == 1
    rec = store.get(p.fingerprint)
    assert rec is not None
    assert rec.status == "inactive"
    assert rec.closed_at is not None
    assert rec.missed_runs == 3
    assert store.count("active") == 0


def test_failed_source_does_not_age_its_postings(store: SeenStore):
    p = _p(source="usajobs")
    _crawl(store, [p], {"usajobs"})
    # usajobs crashed this run: only adzuna counts as a successful crawl.
    _crawl(store, [], {"adzuna"})
    rec = store.get(p.fingerprint)
    assert rec is not None
    assert rec.missed_runs == 0


def test_other_source_seen_does_not_shield_missing_posting(store: SeenStore):
    a = _p(source="usajobs")
    b = _p(source="adzuna", title="Firmware Intern")
    _crawl(store, [a, b], {"usajobs", "adzuna"})
    _crawl(store, [b], {"usajobs", "adzuna"})
    rec_a = store.get(a.fingerprint)
    rec_b = store.get(b.fingerprint)
    assert rec_a is not None and rec_a.missed_runs == 1
    assert rec_b is not None and rec_b.missed_runs == 0


def test_reappearing_posting_is_reactivated(store: SeenStore):
    p = _p()
    _crawl(store, [p], {"usajobs"})
    original = store.get(p.fingerprint)
    assert original is not None
    for _ in range(3):
        _crawl(store, [], {"usajobs"})
    assert store.get(p.fingerprint).status == "inactive"  # type: ignore[union-attr]

    _crawl(store, [p], {"usajobs"})
    rec = store.get(p.fingerprint)
    assert rec is not None
    assert rec.status == "active"
    assert rec.missed_runs == 0
    assert rec.closed_at is None
    assert rec.first_seen == original.first_seen


def test_empty_full_text_does_not_overwrite_stored_text(store: SeenStore):
    p = _p(description="Full body.")
    _crawl(store, [p], {"usajobs"})
    _crawl(store, [_p(description="")], {"usajobs"})
    rec = store.get(p.fingerprint)
    assert rec is not None
    assert rec.full_text == "Full body."
