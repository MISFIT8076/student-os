"""Tests for the day-scheduler + wellbeing pacing."""
from __future__ import annotations

from datetime import date

from app.intelligence.scheduler import schedule_day
from app.schemas import ActionItem


def _item(kind, title):
    return ActionItem(source="test", kind=kind, title=title)


def test_blocks_do_not_overlap():
    items = [_item("deadline", "A"), _item("pull_request", "B"), _item("exam", "C")]
    plan = schedule_day(items, ref=date(2026, 8, 3))
    blocks = plan["blocks"]
    times = [(b["start"], b["end"]) for b in blocks]
    # each block's end <= next block's start
    for (s1, e1), (s2, e2) in zip(times, times[1:]):
        assert e1 <= s2


def test_only_schedulable_kinds_get_blocks():
    items = [_item("email", "mail"), _item("notification", "n"), _item("deadline", "real")]
    plan = schedule_day(items, ref=date(2026, 8, 3))
    titles = [b["title"] for b in plan["blocks"]]
    assert titles == ["real"]  # email/notification are not work blocks


def test_overcommit_defers_and_flags():
    # 8 two-hour exams = 960 min demand; a single 3-hour slot = 180 min available.
    items = [_item("exam", f"Exam {i}") for i in range(8)]
    plan = schedule_day(items, ref=date(2026, 8, 3), free_slots=[(9 * 60, 12 * 60)])
    assert plan["overcommitted"] is True
    assert len(plan["blocks"]) == 1          # only one 120-min exam fits in 180 min
    assert len(plan["overflow"]) == 7
    assert "defer" in plan["advice"].lower()


def test_comfortable_day_fits_everything():
    items = [_item("pull_request", "small PR")]
    plan = schedule_day(items, ref=date(2026, 8, 3))
    assert plan["overcommitted"] is False
    assert len(plan["overflow"]) == 0
    assert len(plan["blocks"]) == 1
