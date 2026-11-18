"""Unit tests for the in-memory cache backend (no Redis needed)."""
from __future__ import annotations

import time

from app.cache import _MemoryBackend


def test_set_get_roundtrip():
    cache = _MemoryBackend()
    cache.set("k", {"a": 1, "items": [1, 2, 3]}, ttl=10)
    assert cache.get("k") == {"a": 1, "items": [1, 2, 3]}


def test_expiry():
    cache = _MemoryBackend()
    cache.set("k", "v", ttl=1)
    assert cache.get("k") == "v"
    # Simulate time passing by rewriting the entry's expiry into the past.
    expires_at, value = cache._store["k"]
    cache._store["k"] = (time.time() - 1, value)
    assert cache.get("k") is None  # expired entries are dropped


def test_delete():
    cache = _MemoryBackend()
    cache.set("k", "v", ttl=10)
    cache.delete("k")
    assert cache.get("k") is None
