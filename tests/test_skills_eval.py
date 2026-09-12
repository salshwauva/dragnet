"""Precision, recall and F1 of the extractor against hand-labeled postings.

`tests/fixtures/skills_eval.json` holds real posting text frozen from dragnet.db.
`expected` is null until a human labels the posting; unlabeled rows are skipped.
Run `pytest tests/test_skills_eval.py -s` to print the numbers for the README.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from dragnet.pipeline.skills import extract

FIXTURE = Path(__file__).parent / "fixtures" / "skills_eval.json"


def evaluate(rows: list[dict[str, object]]) -> tuple[float, float, float, int]:
    tp = fp = fn = labeled = 0
    for row in rows:
        if row["expected"] is None:
            continue
        labeled += 1
        expected = set(row["expected"])  # type: ignore[call-overload]
        got = {s.name for s in extract(f"{row['title']}\n{row['text']}")}
        tp += len(got & expected)
        fp += len(got - expected)
        fn += len(expected - got)
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return precision, recall, f1, labeled


def test_eval_set_metrics() -> None:
    rows = json.loads(FIXTURE.read_text())
    precision, recall, f1, labeled = evaluate(rows)
    if labeled == 0:
        pytest.skip("no labeled postings yet")
    print(f"\nlabeled={labeled} precision={precision:.2f} recall={recall:.2f} f1={f1:.2f}")
    # TODO(human): raise once the labeled set is in and the vocab is tuned.
    assert f1 >= 0.5
