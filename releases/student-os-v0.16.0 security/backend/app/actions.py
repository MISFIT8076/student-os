"""Safe, confirmable actions — the app can *do* things, not just show them.

Everything is two-step by design: `propose()` returns a preview + a one-time
token, and nothing happens until `confirm(token)` is called. This guardrail
means the agent never silently sends an email or changes a calendar on the
student's behalf. Executions are logged to the store.

Supported: draft_reply, add_event, snooze, mark_done. (Draft/event are produced
as previews here; wiring them to real *write-scoped* MCP tools is a drop-in
extension — read-only scopes are intentional for now.)
"""
from __future__ import annotations

import uuid
from datetime import date, timedelta

from app import store

ACTIONS = {"draft_reply", "add_event", "snooze", "mark_done"}

# Pending proposals awaiting confirmation (process-local; fine for one user).
_PENDING: dict[str, dict] = {}


def _preview(action: str, title: str, due: str | None) -> str:
    if action == "draft_reply":
        return (
            f'Draft reply to "{title}":\n\n'
            "Hi,\n\nThank you for reaching out. I'm very interested and would like "
            "to proceed — could we find a suitable time?\n\nBest regards,\n[Your name]"
        )
    if action == "add_event":
        when = due or date.today().isoformat()
        return f'Add calendar event "{title}" on {when} (30 min)'
    if action == "snooze":
        return f'Hide "{title}" until tomorrow'
    return f'Mark "{title}" as done'


def propose(action: str, source: str, kind: str, title: str, due: str | None = None) -> dict:
    """Create a pending action and return a confirmation token + preview."""
    if action not in ACTIONS:
        raise ValueError(f"action must be one of {sorted(ACTIONS)}")
    token = uuid.uuid4().hex
    _PENDING[token] = {"action": action, "source": source, "kind": kind,
                       "title": title, "due": due}
    return {
        "token": token,
        "action": action,
        "preview": _preview(action, title, due),
        "requires_confirmation": True,
    }


def confirm(token: str) -> dict:
    """Execute a previously proposed action. Invalid/used token -> error."""
    proposal = _PENDING.pop(token, None)
    if proposal is None:
        raise KeyError("unknown or already-used confirmation token")

    action = proposal["action"]
    src, kind, title, due = (proposal["source"], proposal["kind"],
                             proposal["title"], proposal["due"])
    result: dict = {"action": action, "title": title}

    if action == "mark_done":
        store.record_feedback(src, kind, title, due, "done")
        result["status"] = "marked done"
    elif action == "snooze":
        store.record_feedback(src, kind, title, due, "snoozed")
        result["status"] = "snoozed until"
        result["until"] = (date.today() + timedelta(days=1)).isoformat()
    elif action == "draft_reply":
        store.record_feedback(src, kind, title, due, "opened")
        result["draft"] = _preview("draft_reply", title, due)
    elif action == "add_event":
        store.record_feedback(src, kind, title, due, "opened")
        result["event"] = {"title": title, "date": due or date.today().isoformat(),
                           "minutes": 30}

    return {"ok": True, "executed": action, "result": result}
