"""Stub scheduler module for v0.2.0 — added in v0.12."""
from __future__ import annotations

from datetime import date


def schedule_day(ranked_items, today: date) -> dict:
    """No-op: day scheduler not yet implemented in v0.2.0."""
    return {"date": str(today), "blocks": [], "note": "scheduler not available in v0.2.0"}
