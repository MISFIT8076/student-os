"""Google Classroom MCP server.

Surfaces pending assignments (with due dates) and recent announcements across
the student's active courses. Uses the shared Google OAuth token (add the
Classroom scopes by re-running the login command after this server is enabled).

Modes:
  * REAL  — STUDENT_OS_MOCK=false AND a Google token with Classroom scopes.
  * MOCK  — otherwise: realistic sample data.

Feasibility note (see docs/ROADMAP.md): the Classroom API only exposes courses
the signed-in student belongs to, and coursework access needs the *.me scopes
used here. Test with a real class early — some institutions restrict API access.
"""
from __future__ import annotations

import sys

from mcp.server.fastmcp import FastMCP

from mcp_servers.common import extraction, google_auth
from mcp_servers.common.util import in_days, mock_enabled, today

mcp = FastMCP("classroom")

API = "https://classroom.googleapis.com/v1"

# Submission states that still need the student's action.
_PENDING = {"NEW", "CREATED", "RECLAIMED_BY_STUDENT"}


def _active_courses() -> list[dict]:
    data = google_auth.authed_get(
        f"{API}/courses",
        {"studentId": "me", "courseStates": "ACTIVE", "pageSize": 10},
    )
    return data.get("courses", [])[:8]


def _due_iso(cw: dict) -> str | None:
    d = cw.get("dueDate")
    if not d:
        return None
    return f"{d['year']:04d}-{d['month']:02d}-{d['day']:02d}"


def _pending_real() -> list[dict]:
    out: list[dict] = []
    for course in _active_courses():
        cid, cname = course["id"], course.get("name", "Course")
        # One call gets every submission for this student in the course.
        subs = google_auth.authed_get(
            f"{API}/courses/{cid}/courseWork/-/studentSubmissions",
            {"userId": "me"},
        ).get("studentSubmissions", [])
        state_by_cw = {s["courseWorkId"]: s.get("state", "") for s in subs}

        cw_list = google_auth.authed_get(
            f"{API}/courses/{cid}/courseWork", {"pageSize": 20}
        ).get("courseWork", [])
        for cw in cw_list:
            state = state_by_cw.get(cw["id"], "NEW")
            if state not in _PENDING:
                continue
            out.append(
                {
                    "kind": "deadline",
                    "title": cw.get("title", "Assignment"),
                    "detail": f"Classroom · {cname}",
                    "url": cw.get("alternateLink", "https://classroom.google.com"),
                    "due": _due_iso(cw),
                    "extra": {"category": "academic", "course": cname},
                }
            )
    return out


def _announcements_real() -> list[dict]:
    out: list[dict] = []
    for course in _active_courses():
        cid, cname = course["id"], course.get("name", "Course")
        anns = google_auth.authed_get(
            f"{API}/courses/{cid}/announcements", {"pageSize": 3}
        ).get("announcements", [])
        for a in anns:
            text = (a.get("text") or "").strip().replace("\n", " ")
            out.append(
                {
                    "kind": "announcement",
                    "title": (text[:70] + "…") if len(text) > 70 else (text or "Announcement"),
                    "detail": f"Classroom · {cname}",
                    "url": a.get("alternateLink", "https://classroom.google.com"),
                    "due": None,
                    "extra": {"course": cname},
                }
            )
    return out


def _guarded(real_fn, mock_data: list[dict]) -> list[dict]:
    """Run the real fetch when possible; otherwise return mock, never crash.

    Either way, run deadline extraction so due dates buried in announcement
    text are recovered.
    """
    if not mock_enabled():
        if google_auth.has_credentials():
            try:
                return extraction.enrich_due(real_fn(), today())
            except Exception as exc:  # noqa: BLE001
                print(f"[classroom] real fetch failed ({exc}); using mock.", file=sys.stderr)
        else:
            print(
                "[classroom] no Google token yet; run the login command. Using mock.",
                file=sys.stderr,
            )
    return extraction.enrich_due([dict(m) for m in mock_data], today())


@mcp.tool()
def list_pending_assignments() -> list[dict]:
    """List assignments the student has not yet turned in, across active courses."""
    return _guarded(_pending_real, _MOCK_ASSIGNMENTS)


@mcp.tool()
def list_announcements() -> list[dict]:
    """List recent announcements from the student's active courses."""
    return _guarded(_announcements_real, _MOCK_ANNOUNCEMENTS)


_MOCK_ASSIGNMENTS = [
    {
        "kind": "deadline",
        "title": "Lab 3 — Process scheduling simulation",
        "detail": "Classroom · Operating Systems",
        "url": "https://classroom.google.com",
        "due": in_days(2),
        "extra": {"category": "academic", "course": "Operating Systems"},
    },
    {
        "kind": "deadline",
        "title": "ER diagram worksheet",
        "detail": "Classroom · DBMS",
        "url": "https://classroom.google.com",
        "due": in_days(4),
        "extra": {"category": "academic", "course": "DBMS"},
    },
]

_MOCK_ANNOUNCEMENTS = [
    {
        "kind": "announcement",
        "title": "No lecture Friday; extra doubt-clearing session Monday.",
        "detail": "Classroom · Operating Systems",
        "url": "https://classroom.google.com",
        "due": None,
        "extra": {"course": "Operating Systems"},
    },
]


if __name__ == "__main__":
    mcp.run()
