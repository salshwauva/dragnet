import tempfile
from pathlib import Path

from dragnet.models import Posting
from dragnet.pipeline.dedupe import fingerprint, split_new
from dragnet.storage import SeenStore


def _p(**kw) -> Posting:
    base = dict(
        source="usajobs",
        source_id="1",
        url="https://x",
        title="Software Intern",
        company="ACo",
        location="Boston, MA",
    )
    base.update(kw)
    return Posting(**base)


def test_fingerprint_stable_across_whitespace():
    a = _p(title="Software Intern", company="ACo")
    b = _p(title="  Software   Intern  ", company="A Co  ")
    fa = fingerprint(a)
    fb = fingerprint(b)
    # Whitespace differs but normalization should fold them. Note: "ACo" vs "A Co" differ
    # because " " separates tokens — punctuation is removed but spaces are preserved.
    # So this test verifies whitespace-only differences ARE folded:
    c = _p(title="  software   intern  ", company="ACo")
    fc = fingerprint(c)
    assert fa == fc
    # "ACo" and "A Co" tokenize differently, so they must NOT collide.
    assert fa != fb


def test_fingerprint_changes_on_company():
    a = _p(company="ACo")
    b = _p(company="BCo")
    assert fingerprint(a) != fingerprint(b)


def test_fingerprint_changes_on_source():
    a = _p(source="usajobs")
    b = _p(source="adzuna")
    assert fingerprint(a) != fingerprint(b)


def test_split_new_first_time_all_new():
    with tempfile.TemporaryDirectory() as td:
        store = SeenStore(Path(td) / "test.db")
        posts = [_p(source_id=str(i), title=f"Role {i}") for i in range(5)]
        new, seen = split_new(posts, store)
        assert len(new) == 5
        assert len(seen) == 0
        store.close()


def test_split_new_second_time_all_seen():
    with tempfile.TemporaryDirectory() as td:
        store = SeenStore(Path(td) / "test.db")
        posts = [_p(source_id=str(i), title=f"Role {i}") for i in range(5)]
        split_new(posts, store)
        store.upsert_many(posts)
        # second run with same postings: all should be seen
        new, seen = split_new(posts, store)
        assert len(new) == 0
        assert len(seen) == 5
        store.close()


def test_record_run_inserts_row():
    with tempfile.TemporaryDirectory() as td:
        store = SeenStore(Path(td) / "test.db")
        store.record_run(total=10, new_count=3)
        rows = store.conn.execute("SELECT total, new_postings FROM runs").fetchall()
        assert rows == [(10, 3)]
        store.close()
