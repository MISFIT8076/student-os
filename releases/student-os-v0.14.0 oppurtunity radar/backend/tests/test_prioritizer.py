"""Unit tests for the context-aware prioritizer.

These are the pieces most worth testing for the viva/report: they encode the
project's actual decision logic and run without launching any MCP server.
"""
from __future__ import annotations

from datetime import date, timedelta

from app.orchestrator.prioritizer import prioritize
from app.schemas import ActionItem, Priority


def _item(**kw) -> ActionItem:
    base = dict(source="test", kind="event", title="x")
    base.update(kw)
    return ActionItem(**base)


REF = date(2026, 7, 28)


def _in(days: int) -> str:
    return (REF + timedelta(days=days)).isoformat()


def test_due_today_outranks_far_event():
    items = [
        _item(kind="event", title="Guild meeting", due=_in(7)),
        _item(kind="deadline", title="Assignment due", due=_in(0)),
    ]
    ranked = prioritize(items, ref=REF)
    assert ranked[0].title == "Assignment due"
    assert ranked[0].priority in {Priority.urgent, Priority.high}


def test_otp_email_ranks_low():
    items = [
        _item(source="gmail", kind="email", title="OTP 123456", raw={"category": "otp"}),
        _item(source="gmail", kind="email", title="Internship closes",
              due=_in(2), raw={"category": "internship"}),
    ]
    ranked = prioritize(items, ref=REF)
    assert ranked[0].title == "Internship closes"
    assert ranked[-1].title == "OTP 123456"


def test_contest_kind_outranks_practice_normally():
    # Non-exam week: a rated contest tomorrow should sit well above a practice nudge.
    items = [
        _item(source="codeforces", kind="practice", title="Codeforces practice"),
        _item(source="codeforces", kind="contest",
              title="Codeforces Round (Div. 2)", due=_in(1)),
    ]
    ranked = prioritize(items, ref=REF)
    assert ranked[0].kind == "contest"
    assert ranked[0].score > ranked[-1].score


def test_exam_week_boosts_academics_and_dampens_contests():
    items = [
        _item(kind="exam", title="DBMS exam", due=_in(3)),
        _item(kind="deadline", title="Codeforces Round registration", due=_in(0)),
        _item(source="gmail", kind="email", title="Assignment rubric",
              due=_in(2), raw={"category": "academic"}),
    ]
    ranked = prioritize(items, ref=REF)
    titles = [i.title for i in ranked]
    # Contest should not be first during exam week even though it's due today.
    assert titles[0] != "Codeforces Round registration"
    contest = next(i for i in ranked if "Codeforces" in i.title)
    academic = next(i for i in ranked if i.title == "Assignment rubric")
    assert academic.score > contest.score
