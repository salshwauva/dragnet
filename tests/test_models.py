from dragnet.models import Posting


def test_posting_construct_minimal():
    p = Posting(source="test", source_id="1", url="https://x", title="T", company="C", location="L")
    assert p.source == "test"
    assert p.is_remote is False
    assert p.intern_signal == 0.0
    assert p.matched_categories == []


def test_signals_summary_default_includes_unclear_start():
    # Default start_date_confidence is "unknown" → emits "Start date unclear".
    p = Posting(source="test", source_id="1", url="https://x", title="T", company="C", location="L")
    assert "Start date unclear" in p.signals_summary()


def test_signals_summary_match_clears_unknown():
    p = Posting(
        source="test",
        source_id="1",
        url="https://x",
        title="T",
        company="C",
        location="L",
        start_date_confidence="match",
    )
    assert "Fall-2026 fit" in p.signals_summary()
    assert "unclear" not in p.signals_summary()


def test_signals_summary_remote_and_citizenship():
    p = Posting(
        source="test",
        source_id="1",
        url="https://x",
        title="T",
        company="C",
        location="L",
        is_remote=True,
        requires_citizenship=True,
    )
    summary = p.signals_summary()
    assert "Remote" in summary
    assert "US Citizen" in summary
