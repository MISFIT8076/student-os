"""Tests for the proactive notifier (dry-run formatting + channel logic)."""
from __future__ import annotations

from datetime import date, timedelta

from app.notifier import build_message, notify
from app.schemas import ActionItem, Priority

REF = date(2026, 8, 3)


def _item(title, priority=Priority.medium, due_days=None):
    due = (REF + timedelta(days=due_days)).isoformat() if due_days is not None else None
    return ActionItem(source="test", kind="deadline", title=title, priority=priority, due=due)


def test_message_lists_due_now_first():
    items = [
        _item("Far task", Priority.medium, due_days=6),
        _item("Assignment due today", Priority.urgent, due_days=0),
        _item("Interview tomorrow", Priority.high, due_days=1),
    ]
    msg = build_message("2 urgent things", "focus on graded work", items, REF)
    assert "Due now:" in msg
    # both today and tomorrow items appear in the alert block
    assert "Assignment due today (due today)" in msg
    assert "Interview tomorrow (due tomorrow)" in msg


def test_message_without_deadlines_has_no_due_block():
    items = [_item("Read a paper"), _item("Refactor code")]
    msg = build_message("calm day", "", items, REF)
    assert "Due now:" not in msg
    assert "Today's top items:" in msg


def test_notify_is_dry_run_without_config(monkeypatch):
    # No telegram/smtp env -> dry-run, never raises.
    for var in ("TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID", "SMTP_HOST",
                "SMTP_USER", "NOTIFY_EMAIL_TO"):
        monkeypatch.delenv(var, raising=False)
    from app.config import get_settings
    get_settings.cache_clear()
    res = notify("hello")
    assert res["channel"] == "dry-run" and res["sent"] is False
    assert res["preview"] == "hello"
