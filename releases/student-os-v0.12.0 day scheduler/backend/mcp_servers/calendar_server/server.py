"""Calendar MCP server.

Modes:
  * REAL  — STUDENT_OS_MOCK=false AND a Google token exists (run
            `python -m mcp_servers.common.google_auth login` once): reads
            upcoming events via the Google Calendar REST API.
  * MOCK  — otherwise: realistic sample events/deadlines.

Shares the OAuth helper (and token) with the Gmail server.
Scope: calendar.readonly.
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone

from mcp.server.fastmcp import FastMCP

from mcp_servers.common import google_auth
from mcp_servers.common.util import in_days, mock_enabled

mcp = FastMCP("calendar")

CAL_API = "https://www.googleapis.com/calendar/v3/calendars/primary/events"

_DEADLINE_HINTS = ("due", "deadline", "submit", "assignment", "registration", "closes")


def _classify(summary: str) -> tuple[str, str]:
    """Return (kind, type) from an event title."""
    s = summary.lower()
    if "exam" in s or "midsem" in s or "quiz" in s:
        return "exam", "event"
    if any(h in s for h in _DEADLINE_HINTS):
        return "deadline", "deadline"
    return "event", "event"


def _fetch_real() -> list[dict]:
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    data = google_auth.authed_get(
        CAL_API,
        {
            "timeMin": now,
            "singleEvents": "true",
            "orderBy": "startTime",
            "maxResults": 15,
        },
    )
    out: list[dict] = []
    for ev in data.get("items", []):
        summary = ev.get("summary", "(busy)")
        kind, type_ = _classify(summary)
        start = ev.get("start", {})
        due = start.get("dateTime") or start.get("date")
        detail = ev.get("location") or (ev.get("description", "")[:80]) or "Google Calendar"
        out.append(
            {
                "kind": kind,
                "title": summary,
                "detail": detail,
                "url": ev.get("htmlLink", "https://calendar.google.com"),
                "due": due,
                "extra": {"type": type_},
            }
        )
    return out


def _fetch_events() -> list[dict]:
    if not mock_enabled():
        if google_auth.has_credentials():
            try:
                return _fetch_real()
            except Exception as exc:  # noqa: BLE001 — fall back, don't crash
                print(f"[calendar] real fetch failed ({exc}); using mock.", file=sys.stderr)
        else:
            print(
                "[calendar] no Google token yet; run the login command. Using mock.",
                file=sys.stderr,
            )
    return _MOCK_EVENTS


@mcp.tool()
def list_upcoming_events() -> list[dict]:
    """List upcoming calendar events (classes, meetings, exams)."""
    return [e for e in _fetch_events() if e["extra"].get("type") == "event"]


@mcp.tool()
def list_deadlines() -> list[dict]:
    """List upcoming deadlines (assignments, exams, contest registrations)."""
    return [e for e in _fetch_events() if e["extra"].get("type") == "deadline"]


_MOCK_EVENTS = [
    {
        "kind": "deadline",
        "title": "OS Assignment 4 submission",
        "detail": "Google Classroom · Operating Systems",
        "url": "https://classroom.google.com",
        "due": in_days(1),
        "extra": {"type": "deadline"},
    },
    {
        "kind": "deadline",
        "title": "Codeforces Round registration closes",
        "detail": "Div 2 · rated",
        "url": "https://codeforces.com/contests",
        "due": in_days(0),
        "extra": {"type": "deadline"},
    },
    {
        "kind": "exam",
        "title": "DBMS mid-semester exam",
        "detail": "Room C-204 · 09:00",
        "url": "https://classroom.google.com",
        "due": in_days(5),
        "extra": {"type": "event"},
    },
    {
        "kind": "event",
        "title": "FYP sync with Dr. Varsha",
        "detail": "Cabin 12 · weekly guide meeting",
        "url": "https://calendar.google.com",
        "due": in_days(2),
        "extra": {"type": "event"},
    },
]


if __name__ == "__main__":
    mcp.run()
