"""Tests for MongoDB persistence integration and fallback logic."""
from __future__ import annotations

from unittest.mock import MagicMock


def test_mongodb_dual_write_custom_task(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'test.db'}")
    from app import store
    from app.config import get_settings

    get_settings.cache_clear()
    store._engine.cache_clear()

    mock_db = MagicMock()
    mock_tasks = MagicMock()
    mock_db.__getitem__.return_value = mock_tasks

    monkeypatch.setattr(store, "_mongo_db", lambda: mock_db)

    task = store.create_custom_task(
        title="MongoDB Unit Test Task",
        detail="Check dual write",
        priority="high",
    )
    assert task["title"] == "MongoDB Unit Test Task"
    mock_db.__getitem__.assert_called_with("custom_tasks")
    assert mock_tasks.replace_one.called


def test_mongodb_mark_task_done(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'test.db'}")
    from app import store
    from app.config import get_settings

    get_settings.cache_clear()
    store._engine.cache_clear()

    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_db.__getitem__.return_value = mock_collection

    monkeypatch.setattr(store, "_mongo_db", lambda: mock_db)

    assert store.mark_task_done("personal", "Test Mongo Done")
    assert mock_collection.update_one.called
    assert mock_collection.insert_one.called


def test_mongodb_fallback_on_error(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'test.db'}")
    from app import store
    from app.config import get_settings

    get_settings.cache_clear()
    store._engine.cache_clear()

    mock_db = MagicMock()
    mock_tasks = MagicMock()
    mock_tasks.find.side_effect = Exception("MongoDB Network Timeout")
    mock_db.__getitem__.return_value = mock_tasks

    monkeypatch.setattr(store, "_mongo_db", lambda: mock_db)

    # Creating task writes to SQLite despite MongoDB mock failure if error happens
    # Here let's test get_active_custom_tasks fallback to SQLite
    active = store.get_active_custom_tasks()
    assert isinstance(active, list)
