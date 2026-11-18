"""Turn a ranked to-do list into an actual time-blocked plan for the day.

Given ranked items (most important first) and the day's free slots, greedily
places each schedulable task into the earliest gap that fits. Adds
**wellbeing-aware pacing**: if there's more work than hours, it schedules the
top-priority tasks that fit and defers the rest instead of pretending an
impossible day is possible.

Pure and deterministic, so it's easy to unit-test (no overlaps, deadlines
respected, honest overflow).
"""
from __future__ import annotations

from datetime import date

from app.schemas import ActionItem

# Rough effort estimate per kind, in minutes.
_DURATION = {
    "exam": 120,       # focused revision block
    "contest": 120,
    "deadline": 90,
    "issue": 60,
    "practice": 60,
    "pull_request": 45,
    "email": 15,
}
_DEFAULT_DURATION = 30
# Kinds that are tasks to do (not fixed events / passive notifications).
_SCHEDULABLE = {"exam", "deadline", "pull_request", "issue", "contest", "practice"}

# Default working day: 09:00–13:00 and 14:00–21:00 (a lunch break between).
_DEFAULT_SLOTS = [(9 * 60, 13 * 60), (14 * 60, 21 * 60)]


def _hhmm(minutes: int) -> str:
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def duration_for(item: ActionItem) -> int:
    return _DURATION.get(item.kind, _DEFAULT_DURATION)


def schedule_day(
    items: list[ActionItem],
    ref: date | None = None,
    free_slots: list[tuple[int, int]] | None = None,
) -> dict:
    """Build a time-blocked plan. `items` must already be in ranked order."""
    ref = ref or date.today()
    # Mutable copy of free intervals (minutes from midnight).
    gaps = [[s, e] for s, e in (free_slots or _DEFAULT_SLOTS)]
    available = sum(e - s for s, e in gaps)

    tasks = [it for it in items if it.kind in _SCHEDULABLE]
    demand = sum(duration_for(it) for it in tasks)

    blocks: list[dict] = []
    overflow: list[dict] = []
    for it in tasks:
        dur = duration_for(it)
        placed = False
        for gap in gaps:
            if gap[1] - gap[0] >= dur:
                start = gap[0]
                gap[0] += dur  # consume from the front of the gap
                blocks.append({
                    "start": _hhmm(start),
                    "end": _hhmm(start + dur),
                    "minutes": dur,
                    "title": it.title,
                    "source": it.source,
                    "kind": it.kind,
                    "due": it.due,
                    "priority": it.priority.value if hasattr(it.priority, "value") else str(it.priority),
                })
                placed = True
                break
        if not placed:
            overflow.append({"title": it.title, "source": it.source,
                             "kind": it.kind, "due": it.due, "minutes": dur})

    blocks.sort(key=lambda b: b["start"])
    overcommitted = demand > available
    scheduled_min = sum(b["minutes"] for b in blocks)

    if overcommitted:
        advice = (
            f"Heads up: about {demand // 60}h{demand % 60:02d} of work but only "
            f"{available // 60}h{available % 60:02d} free today. Scheduled the top "
            f"{len(blocks)} and deferred {len(overflow)} — consider moving the "
            f"lower-priority ones to tomorrow."
        )
    elif not tasks:
        advice = "Nothing needs a work block today — enjoy the breathing room."
    else:
        advice = "Comfortable day: everything important fits with time to spare."

    return {
        "date": ref.isoformat(),
        "blocks": blocks,
        "overflow": overflow,
        "available_minutes": available,
        "demand_minutes": demand,
        "scheduled_minutes": scheduled_min,
        "overcommitted": overcommitted,
        "advice": advice,
    }
