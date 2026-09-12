from datetime import UTC, datetime, timedelta
from typing import Any

from dragnet.config import Config
from dragnet.models import Posting
from dragnet.pipeline.score import (
    category_score,
    fit_bonus,
    location_score,
    recency_score,
    score_one,
)


def _cfg() -> Config:
    return Config(
        category_weights={"swe": 1.0, "ml": 1.5, "embedded": 1.0},
    )


def _p(**kwargs) -> Posting:
    base: dict[str, Any] = dict(
        source="t", source_id="1", url="https://x", title="T", company="C", location=""
    )
    base.update(kwargs)
    return Posting(**base)


def test_location_remote_wins():
    p = _p(is_remote=True, location="Anywhere")
    assert location_score(p, _cfg()) == 100


def test_location_boston_bucket():
    p = _p(location="Cambridge, MA")
    assert location_score(p, _cfg()) == 70


def test_location_dc_bucket():
    p = _p(location="Reston, VA")
    assert location_score(p, _cfg()) == 50


def test_location_international_low():
    p = _p(location="London, UK")
    assert location_score(p, _cfg()) == 0


def test_recency_fresh_high():
    p = _p(posted_at=datetime.now(UTC))
    assert recency_score(p, _cfg()) == 50


def test_recency_old_zero():
    p = _p(posted_at=datetime.now(UTC) - timedelta(days=100))
    assert recency_score(p, _cfg()) == 0


def test_category_score_weighted():
    p = _p(matched_categories=["ml"])
    # 25 (base) * 1.5 (ml weight) = 37.5
    assert category_score(p, _cfg()) == 37.5


def test_fit_bonus_stacks():
    p = _p(requires_citizenship=True, requires_clearance=True)
    assert fit_bonus(p, _cfg()) == 50  # 20 + 30


def test_score_one_composes():
    p = _p(
        location="Cambridge, MA",
        posted_at=datetime.now(UTC),
        matched_categories=["swe"],
        requires_citizenship=True,
    )
    s = score_one(p, _cfg())
    # 70 (boston) + 50 (fresh) + 25 (swe) + 20 (citizenship) = 165
    assert s == 165.0
    assert p.score == 165.0
