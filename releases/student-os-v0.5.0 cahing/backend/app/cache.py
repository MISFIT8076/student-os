"""Caching for the expensive MCP fan-out.

`gather_action_items()` launches every MCP server and hits every API. Within a
short window that work is wasteful, so we cache the merged result. This is the
"Redis for caching" line in the proposal's tech stack — but with a twist:

    * If REDIS_URL is set and reachable → use Redis (production path).
    * Otherwise → an in-process TTL cache (so it still works with zero setup).

The cache stores plain JSON; the orchestrator re-hydrates pydantic models.
"""
from __future__ import annotations

import json
import threading
import time
from typing import Any

from app.config import get_settings


class _MemoryBackend:
    """Thread-safe in-process cache with per-key expiry."""

    name = "memory"

    def __init__(self) -> None:
        self._store: dict[str, tuple[float, Any]] = {}
        self._lock = threading.Lock()

    def get(self, key: str) -> Any | None:
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            expires_at, value = entry
            if time.time() > expires_at:
                self._store.pop(key, None)
                return None
            return value

    def set(self, key: str, value: Any, ttl: int) -> None:
        with self._lock:
            self._store[key] = (time.time() + ttl, value)

    def delete(self, key: str) -> None:
        with self._lock:
            self._store.pop(key, None)


class _RedisBackend:
    """Redis-backed cache. Constructor raises if the server is unreachable."""

    name = "redis"

    def __init__(self, url: str) -> None:
        import redis  # lazy import so redis is optional

        self._r = redis.Redis.from_url(url, decode_responses=True)
        self._r.ping()  # fail fast → caller falls back to memory

    def get(self, key: str) -> Any | None:
        raw = self._r.get(key)
        return json.loads(raw) if raw else None

    def set(self, key: str, value: Any, ttl: int) -> None:
        self._r.setex(key, ttl, json.dumps(value))

    def delete(self, key: str) -> None:
        self._r.delete(key)


_backend: _MemoryBackend | _RedisBackend | None = None


def get_cache() -> _MemoryBackend | _RedisBackend:
    """Return the process-wide cache, choosing Redis when available."""
    global _backend
    if _backend is None:
        settings = get_settings()
        if settings.redis_url:
            try:
                _backend = _RedisBackend(settings.redis_url)
            except Exception:  # noqa: BLE001 — Redis down → degrade to memory
                _backend = _MemoryBackend()
        else:
            _backend = _MemoryBackend()
    return _backend
