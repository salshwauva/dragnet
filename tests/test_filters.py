from dragnet.config import Config, FilterConfig
from dragnet.models import Posting
from dragnet.pipeline.filters import annotate, keep


def _cfg(**kwargs) -> Config:
    cfg = Config(
        categories={
            "swe": ["software engineer", "swe", "backend"],
            "ml": ["machine learning", "ml engineer"],
        },
        filters=FilterConfig(intern_required=True, drop_summer_2026=True),
    )
    return cfg


def _post(title: str, body: str = "", location: str = "Boston, MA") -> Posting:
    return Posting(
        source="t",
        source_id="1",
        url="https://x",
        title=title,
        company="ACo",
        location=location,
        description=body,
    )


def test_intern_signal_from_title():
    p = _post("Software Engineering Intern")
    annotate(p, _cfg())
    assert p.intern_signal == 1.0


def test_intern_signal_from_body_only():
    p = _post("Software Engineer", body="This role is open to undergraduate students.")
    annotate(p, _cfg())
    assert p.intern_signal == 0.5


def test_intern_coordinator_excluded():
    p = _post("Internship Coordinator", body="manage interns")
    annotate(p, _cfg())
    assert p.intern_signal == 0.0
    assert not keep(p, _cfg())


def test_summer_2026_only_is_dropped():
    p = _post("Software Intern", body="This is a Summer 2026 internship only.")
    annotate(p, _cfg())
    assert p.start_date_confidence == "non-fit"
    assert not keep(p, _cfg())


def test_fall_2026_match():
    p = _post("Software Intern", body="Start date: Fall 2026.")
    annotate(p, _cfg())
    assert p.start_date_confidence == "match"
    assert p.start_date_raw is not None
    assert "fall 2026" in p.start_date_raw.lower()


def test_unknown_start_date_kept():
    p = _post("Software Intern", body="Join us!")
    annotate(p, _cfg())
    assert p.start_date_confidence == "unknown"
    assert keep(p, _cfg())


def test_clearance_detection():
    p = _post("Cleared Software Intern", body="Active TS/SCI clearance required.")
    annotate(p, _cfg())
    assert p.requires_clearance is True


def test_category_match():
    p = _post("Software Engineering Intern", body="Backend role.")
    annotate(p, _cfg())
    assert "swe" in p.matched_categories


def test_remote_detection_from_body():
    p = _post("Software Intern", body="This is a fully remote position.", location="Remote")
    annotate(p, _cfg())
    assert p.is_remote is True
