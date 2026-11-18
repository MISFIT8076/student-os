"""Tests for the runtime learned ranker (uses the trained weights file)."""
from __future__ import annotations

from datetime import date, timedelta

import pytest

from app.intelligence.learned_ranker import WEIGHTS, LearnedRanker
from app.schemas import ActionItem

REF = date(2026, 7, 31)


def _item(**kw) -> ActionItem:
    base = dict(source="test", kind="event", title="x")
    base.update(kw)
    return ActionItem(**base)


def _due(days: int) -> str:
    return (REF + timedelta(days=days)).isoformat()


@pytest.mark.skipif(not WEIGHTS.exists(), reason="train the model first: python -m app.intelligence.train")
def test_available_when_trained():
    assert LearnedRanker().available()


@pytest.mark.skipif(not WEIGHTS.exists(), reason="model not trained")
def test_ranks_urgent_coursework_above_noise():
    items = [
        _item(source="gmail", kind="email", title="Your OTP", raw={"category": "otp"}),
        _item(source="calendar", kind="exam", title="OS exam", due=_due(1)),
        _item(source="calendar", kind="deadline", title="Assignment due",
              due=_due(1), raw={"category": "academic"}),
    ]
    ranked = LearnedRanker().rank(items, ref=REF)
    assert ranked[0].kind in {"exam", "deadline"}
    assert ranked[-1].title == "Your OTP"
