"""Pytest configuration and global fixtures for backend tests."""
from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def disable_mongodb_in_tests(monkeypatch):
    """Ensure automated test runs never write to or read from live MongoDB Atlas."""
    monkeypatch.setenv("MONGODB_URI", "")
    from app.config import get_settings
    get_settings.cache_clear()
    try:
        from app.store import _mongo_db
        _mongo_db.cache_clear()
    except Exception:
        pass
