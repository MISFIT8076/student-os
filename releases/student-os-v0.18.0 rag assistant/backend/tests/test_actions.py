"""Tests for the propose->confirm action guardrail."""
from __future__ import annotations

import pytest

from app import actions


def test_propose_returns_token_and_preview():
    p = actions.propose("draft_reply", "gmail", "email", "Internship at Rubrik")
    assert p["requires_confirmation"] is True
    assert p["token"]
    assert "Draft reply" in p["preview"]


def test_confirm_executes_once_then_token_is_dead():
    p = actions.propose("mark_done", "calendar", "deadline", "Assignment")
    res = actions.confirm(p["token"])
    assert res["ok"] and res["executed"] == "mark_done"
    # token is single-use
    with pytest.raises(KeyError):
        actions.confirm(p["token"])


def test_unknown_token_rejected():
    with pytest.raises(KeyError):
        actions.confirm("not-a-real-token")


def test_invalid_action_rejected():
    with pytest.raises(ValueError):
        actions.propose("delete_everything", "gmail", "email", "x")


def test_add_event_produces_event_preview():
    p = actions.propose("add_event", "calendar", "event", "FYP meeting", due="2026-08-05")
    res = actions.confirm(p["token"])
    assert res["result"]["event"]["date"] == "2026-08-05"
