"""Tests for the progress/habit aggregation."""
from __future__ import annotations


def _fresh_store(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'prog.db'}")
    from app import store
    from app.config import get_settings
    get_settings.cache_clear(); store._engine.cache_clear()
    return store


def test_progress_streak_and_funnel(tmp_path, monkeypatch):
    store = _fresh_store(tmp_path, monkeypatch)
    try:
        store.record_feedback("calendar", "deadline", "Assignment", None, "done")
        store.record_feedback("github", "pull_request", "PR", None, "opened")
        store.set_opportunity_status("gmail", "Internship", "2026-08-05",
                                     "email", "internship", "applied")
        p = store.get_progress()
        assert p["done_streak_days"] >= 1        # completed something today
        assert p["actions"].get("done") == 1
        assert p["total_actions"] == 2
        assert p["application_funnel"].get("applied") == 1
    finally:
        from app.config import get_settings
        get_settings.cache_clear(); store._engine.cache_clear()
