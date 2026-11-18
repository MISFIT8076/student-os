"""Codeforces MCP server.

Uses the official public Codeforces API (https://codeforces.com/api/).
Upcoming contests need no authentication; the practice reminder uses the
student's handle from the CODEFORCES_HANDLE env var.

This server is proof that a new platform drops in without touching the
orchestrator, prioritizer, API, or UI — you only add this file and one line
in servers.json.

Modes:
  * REAL  — STUDENT_OS_MOCK=false: live API calls (contests are public;
            the reminder additionally needs CODEFORCES_HANDLE).
  * MOCK  — otherwise: realistic sample data.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone

import httpx
from mcp.server.fastmcp import FastMCP

from mcp_servers.common.util import in_days, mock_enabled

mcp = FastMCP("codeforces")

CF_API = "https://codeforces.com/api"


def _handle() -> str:
    return os.getenv("CODEFORCES_HANDLE", "")


def _get(path: str, params: dict | None = None):
    """GET the Codeforces API with TLS verification ON. Raises on error."""
    with httpx.Client(base_url=CF_API, timeout=15) as client:
        resp = client.get(path, params=params or {})
        resp.raise_for_status()
        body = resp.json()
    if body.get("status") != "OK":
        raise RuntimeError(body.get("comment", "Codeforces API returned non-OK"))
    return body["result"]


def _fmt_start(epoch: int) -> str:
    return datetime.fromtimestamp(epoch, tz=timezone.utc).isoformat()


# ── tools ──────────────────────────────────────────────────────────────────
@mcp.tool()
def list_upcoming_contests() -> list[dict]:
    """List upcoming Codeforces contests (phase BEFORE), soonest first."""
    if mock_enabled():
        return _MOCK_CONTESTS
    try:
        contests = _get("/contest.list", {"gym": "false"})
        upcoming = [c for c in contests if c.get("phase") == "BEFORE"]
        upcoming.sort(key=lambda c: c.get("startTimeSeconds", 0))
        out = []
        for c in upcoming[:6]:
            hours = round(c.get("durationSeconds", 0) / 3600, 1)
            out.append(
                {
                    "kind": "contest",
                    "title": c["name"],
                    "detail": f"Codeforces · {hours}h · rated round",
                    "url": f"https://codeforces.com/contests/{c['id']}",
                    "due": _fmt_start(c["startTimeSeconds"]),
                    "extra": {"contest_id": c["id"]},
                }
            )
        return out
    except Exception as exc:  # noqa: BLE001 — degrade to mock
        return [_error_item("list_upcoming_contests", exc)] + _MOCK_CONTESTS


@mcp.tool()
def practice_reminder() -> list[dict]:
    """Nudge to practice if the student hasn't solved a problem recently.

    Returns a single reminder item when the last accepted submission is older
    than two days; otherwise returns nothing. Needs CODEFORCES_HANDLE.
    """
    if mock_enabled():
        return _MOCK_REMINDER
    handle = _handle()
    if not handle:
        return []  # nothing to check without a handle
    try:
        subs = _get("/user.status", {"handle": handle, "from": 1, "count": 50})
        accepted = [s for s in subs if s.get("verdict") == "OK"]
        if not accepted:
            return _reminder("You have no solved problems yet — try an easy one today.")
        last = max(s["creationTimeSeconds"] for s in accepted)
        days = (datetime.now(timezone.utc).timestamp() - last) / 86400
        if days >= 2:
            return _reminder(
                f"No solved problem in {int(days)} days — keep the streak alive."
            )
        return []
    except Exception as exc:  # noqa: BLE001
        return [_error_item("practice_reminder", exc)]


def _reminder(msg: str) -> list[dict]:
    return [
        {
            "kind": "practice",
            "title": "Codeforces practice",
            "detail": msg,
            "url": f"https://codeforces.com/problemset",
            "due": None,
            "extra": {},
        }
    ]


def _error_item(tool: str, exc: Exception) -> dict:
    return {
        "kind": "error",
        "title": f"Codeforces API error in {tool}",
        "detail": f"{type(exc).__name__}: {exc}. Showing sample data instead.",
        "url": None,
        "due": None,
        "extra": {},
    }


# ── mock data ────────────────────────────────────────────────────────────
_MOCK_CONTESTS = [
    {
        "kind": "contest",
        "title": "Codeforces Round (Div. 2)",
        "detail": "Codeforces · 2.0h · rated round",
        "url": "https://codeforces.com/contests",
        "due": in_days(1),
        "extra": {"contest_id": 9001},
    },
    {
        "kind": "contest",
        "title": "Educational Codeforces Round",
        "detail": "Codeforces · 2.0h · rated round",
        "url": "https://codeforces.com/contests",
        "due": in_days(4),
        "extra": {"contest_id": 9002},
    },
]

_MOCK_REMINDER = [
    {
        "kind": "practice",
        "title": "Codeforces practice",
        "detail": "No solved problem in 3 days — keep the streak alive.",
        "url": "https://codeforces.com/problemset",
        "due": None,
        "extra": {},
    }
]


if __name__ == "__main__":
    mcp.run()
