"""Tests for the opportunity radar (classification + status tracking)."""
from __future__ import annotations

import pytest

from app.intelligence.opportunities import classify_opportunity, collect_opportunities
from app.schemas import ActionItem


def _item(**kw):
    base = dict(source="gmail", kind="email", title="x")
    base.update(kw)
    return ActionItem(**base)


def test_classification():
    assert classify_opportunity(_item(title="Summer internship at Rubrik",
                                      raw={"category": "internship"})) == "internship"
    assert classify_opportunity(_item(title="Merit scholarship — apply now")) == "scholarship"
    assert classify_opportunity(_item(title="Smart India Hackathon invite")) == "hackathon"
    assert classify_opportunity(_item(source="codeforces", kind="contest",
                                      title="Codeforces Round")) == "contest"
    assert classify_opportunity(_item(title="Your OTP is 1234",
                                      raw={"category": "otp"})) is None


def test_collect_filters_and_defaults_status(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'opp.db'}")
    from app import store
    from app.config import get_settings
    get_settings.cache_clear(); store._engine.cache_clear()
    try:
        items = [
            _item(title="Internship deadline", due="2026-08-05", raw={"category": "internship"}),
            _item(title="Weekly newsletter", raw={"category": "other"}),
        ]
        opps = collect_opportunities(items)
        assert [o["title"] for o in opps] == ["Internship deadline"]
        assert opps[0]["status"] == "new"

        # After saving a status, it should be reflected.
        store.set_opportunity_status("gmail", "Internship deadline", "2026-08-05",
                                     "email", "internship", "applied")
        opps2 = collect_opportunities(items)
        assert opps2[0]["status"] == "applied"
    finally:
        from app.config import get_settings as gs
        gs.cache_clear(); store._engine.cache_clear()


def test_invalid_status_rejected(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'opp2.db'}")
    from app import store
    from app.config import get_settings
    get_settings.cache_clear(); store._engine.cache_clear()
    try:
        with pytest.raises(ValueError):
            store.set_opportunity_status("gmail", "x", None, "email", "internship", "bogus")
    finally:
        get_settings.cache_clear(); store._engine.cache_clear()
