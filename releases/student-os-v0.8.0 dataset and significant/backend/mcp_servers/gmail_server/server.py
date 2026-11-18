"""Gmail MCP server.

Modes:
  * REAL  — STUDENT_OS_MOCK=false AND a Google token exists (run
            `python -m mcp_servers.common.google_auth login` once): reads
            unread primary mail via the Gmail REST API.
  * MOCK  — otherwise: realistic sample mail, so the pipeline never breaks.

Uses the shared OAuth helper in mcp_servers/common/google_auth.py (Gmail and
Calendar share one token). Scope: gmail.readonly.
"""
from __future__ import annotations

import sys

from mcp.server.fastmcp import FastMCP

from mcp_servers.common import extraction, google_auth
from mcp_servers.common.util import in_days, mock_enabled, today

mcp = FastMCP("gmail")

GMAIL_API = "https://gmail.googleapis.com/gmail/v1/users/me"

_INTERNSHIP_HINTS = (
    "intern", "internship", "hiring", "recruiter", "opportunity",
    "placement", "job", "sde", "career",
)
_ACADEMIC_HINTS = ("assignment", "exam", "lecture", "class", "rubric", "submission")


def _categorize(subject: str, sender: str) -> str:
    text = f"{subject} {sender}".lower()
    if "otp" in text or "verification code" in text or "one-time" in text:
        return "otp"
    if any(h in text for h in _INTERNSHIP_HINTS):
        return "internship"
    if ".edu" in sender.lower() or any(h in text for h in _ACADEMIC_HINTS):
        return "academic"
    return "other"


def _header(headers: list[dict], name: str) -> str:
    for h in headers:
        if h.get("name", "").lower() == name.lower():
            return h.get("value", "")
    return ""


def _fetch_real() -> list[dict]:
    """Read unread primary mail via the Gmail API and normalize it."""
    listing = google_auth.authed_get(
        f"{GMAIL_API}/messages",
        {"q": "is:unread category:primary", "maxResults": 12},
    )
    out: list[dict] = []
    for ref in listing.get("messages", []):
        msg = google_auth.authed_get(
            f"{GMAIL_API}/messages/{ref['id']}",
            {"format": "metadata", "metadataHeaders": ["Subject", "From"]},
        )
        headers = msg.get("payload", {}).get("headers", [])
        subject = _header(headers, "Subject") or "(no subject)"
        sender = _header(headers, "From")
        out.append(
            {
                "kind": "email",
                "title": subject,
                "detail": sender,
                "url": f"https://mail.google.com/mail/u/0/#inbox/{ref['id']}",
                "due": None,
                "extra": {"category": _categorize(subject, sender), "unread": True},
            }
        )
    return out


def _fetch_unread() -> list[dict]:
    if not mock_enabled():
        if google_auth.has_credentials():
            try:
                # Extraction fills deadlines hidden in real email subjects.
                return extraction.enrich_due(_fetch_real(), today())
            except Exception as exc:  # noqa: BLE001 — fall back, don't crash
                print(f"[gmail] real fetch failed ({exc}); using mock.", file=sys.stderr)
        else:
            print(
                "[gmail] no Google token yet; run the login command. Using mock.",
                file=sys.stderr,
            )
    return extraction.enrich_due([dict(m) for m in _MOCK_MAIL], today())


@mcp.tool()
def list_priority_unread() -> list[dict]:
    """List unread, high-signal emails (internships, notices, deadlines)."""
    return _fetch_unread()


@mcp.tool()
def list_internship_mail() -> list[dict]:
    """List unread emails that look internship/placement related."""
    return [m for m in _fetch_unread() if m["extra"].get("category") == "internship"]


_MOCK_MAIL = [
    {
        "kind": "email",
        "title": "Summer Internship — Application closes soon (Rubrik)",
        "detail": "Recruiting <careers@rubrik.com> · apply before the window shuts",
        "url": "https://mail.google.com/mail/u/0/#inbox",
        "due": in_days(2),
        "extra": {"category": "internship", "unread": True},
    },
    {
        "kind": "email",
        "title": "OS assignment 4 rubric updated",
        "detail": "Dr. Varsha Sisaudia <varsha@college.edu>",
        "url": "https://mail.google.com/mail/u/0/#inbox",
        "due": in_days(3),
        "extra": {"category": "academic", "unread": True},
    },
    {
        "kind": "email",
        "title": "Your OTP for placement portal is 481920",
        "detail": "no-reply@placements.edu · expires in 10 min",
        "url": "https://mail.google.com/mail/u/0/#inbox",
        "due": None,
        "extra": {"category": "otp", "unread": True},
    },
    {
        "kind": "email",
        "title": "Recruiter viewed your profile — SDE Intern role open",
        "detail": "LinkedIn <jobs@linkedin.com>",
        "url": "https://mail.google.com/mail/u/0/#inbox",
        "due": None,
        "extra": {"category": "internship", "unread": True},
    },
    {
        # No explicit due date — the deadline lives in the text and is
        # recovered by the NLP extractor (mcp_servers/common/extraction.py).
        "kind": "email",
        "title": "Scholarship portal — apply by Friday",
        "detail": "Financial Aid Office <aid@college.edu>",
        "url": "https://mail.google.com/mail/u/0/#inbox",
        "due": None,
        "extra": {"category": "academic", "unread": True},
    },
]


if __name__ == "__main__":
    mcp.run()
