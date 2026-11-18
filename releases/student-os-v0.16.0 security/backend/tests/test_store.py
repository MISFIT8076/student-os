"""Tests for the persistence layer, against a throwaway SQLite file."""
from __future__ import annotations

import pytest


def _fresh_store(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'test.db'}")
    from app import store
    from app.config import get_settings

    get_settings.cache_clear()
    store._engine.cache_clear()
    return store


def test_feedback_and_stats(tmp_path, monkeypatch):
    store = _fresh_store(tmp_path, monkeypatch)
    try:
        assert store.record_feedback("gmail", "email", "Internship", "2026-08-01", "done")
        assert store.record_feedback("github", "pull_request", "PR #42", None, "opened")
        stats = store.get_stats()
        assert stats["feedback_total"] == 2
        assert stats["feedback_by_action"].get("done") == 1
        assert stats["feedback_by_source"].get("gmail") == 1
    finally:
        from app.config import get_settings
        get_settings.cache_clear()
        store._engine.cache_clear()


def test_invalid_action_rejected(tmp_path, monkeypatch):
    store = _fresh_store(tmp_path, monkeypatch)
    try:
        with pytest.raises(ValueError):
            store.record_feedback("gmail", "email", "x", None, "not-an-action")
    finally:
        from app.config import get_settings
        get_settings.cache_clear()
        store._engine.cache_clear()


def test_item_key_stable(tmp_path, monkeypatch):
    store = _fresh_store(tmp_path, monkeypatch)
    k1 = store.item_key("gmail", "Internship", "2026-08-01")
    k2 = store.item_key("gmail", "internship ", "2026-08-01")  # case/space-insensitive
    assert k1 == k2
