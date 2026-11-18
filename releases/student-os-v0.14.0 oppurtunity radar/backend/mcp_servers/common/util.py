"""Small utilities shared by every MCP server."""
from __future__ import annotations

import os
from datetime import date, datetime, timedelta, timezone


def mock_enabled() -> bool:
    """Servers are launched as subprocesses, so they read the flag from env.

    Defaults to True: with no credentials the server serves sample data.
    """
    return os.getenv("STUDENT_OS_MOCK", "true").lower() in {"1", "true", "yes"}


def today() -> date:
    return datetime.now(timezone.utc).date()


def in_days(n: int) -> str:
    """ISO date string n days from today (n may be negative)."""
    return (today() + timedelta(days=n)).isoformat()


def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
