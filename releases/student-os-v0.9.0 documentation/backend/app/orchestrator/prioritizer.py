"""Context-aware prioritizer.

Turns a flat list of ActionItems from many sources into a single ranked list.
The score combines (a) what kind of thing it is, (b) how soon it is due, and
(c) the student's current context — e.g. during exam week, academic work is
boosted and contests are dialed down. This is the "Context-Aware
Prioritization" feature from the proposal, kept deliberately transparent and
rule-based so it can be explained in a viva and later swapped for a model.
"""
from __future__ import annotations

from datetime import date

from app.schemas import ActionItem, Priority

# Base importance by item kind.
_KIND_WEIGHT = {
    "exam": 6.0,
    "deadline": 5.0,
    "pull_request": 3.0,
    "contest": 3.0,
    "notification": 2.5,
    "issue": 2.0,
    "email": 2.0,
    "practice": 1.5,
    "announcement": 1.5,
    "event": 1.0,
    "error": 0.0,
}

# Extra weight by email category (from the Gmail server's `extra`).
_EMAIL_CATEGORY_WEIGHT = {
    "internship": 4.0,
    "academic": 2.0,
    "otp": -3.0,  # time-sensitive but not a task to plan around
}


def _days_until(due: str | None, ref: date) -> int | None:
    if not due:
        return None
    try:
        d = date.fromisoformat(due[:10])
    except ValueError:
        return None
    return (d - ref).days


def _due_boost(days: int | None) -> float:
    if days is None:
        return 0.0
    if days <= 0:
        return 6.0  # due today or overdue
    if days == 1:
        return 4.0
    if days <= 3:
        return 2.0
    if days <= 7:
        return 1.0
    return 0.0


def _exam_week(items: list[ActionItem], ref: date) -> bool:
    for it in items:
        if it.kind == "exam":
            d = _days_until(it.due, ref)
            if d is not None and 0 <= d <= 5:
                return True
    return False


# Keywords that mark an item as competitive-programming practice rather than
# graded coursework (used to dial contests down during exam week).
_CONTEST_HINTS = ("contest", "codeforces", "leetcode", "hackathon", "round")


def _is_contest(item: ActionItem) -> bool:
    text = f"{item.title} {item.detail}".lower()
    return any(h in text for h in _CONTEST_HINTS)


def _is_graded(item: ActionItem) -> bool:
    return item.kind in {"exam", "deadline"} or item.raw.get("category") == "academic"


def _to_priority(score: float) -> Priority:
    if score >= 9:
        return Priority.urgent
    if score >= 6:
        return Priority.high
    if score >= 3:
        return Priority.medium
    return Priority.low


def prioritize(items: list[ActionItem], ref: date | None = None) -> list[ActionItem]:
    """Score, tag, and sort items by descending priority."""
    ref = ref or date.today()
    exam_week = _exam_week(items, ref)

    for it in items:
        score = _KIND_WEIGHT.get(it.kind, 1.0)
        days = _days_until(it.due, ref)
        score += _due_boost(days)

        if it.kind == "email":
            category = str(it.raw.get("category", ""))
            score += _EMAIL_CATEGORY_WEIGHT.get(category, 0.0)

        # Context-aware adjustments. During exam week, graded work is pushed up
        # and competitive practice is pushed down — but a contest is classified
        # as a contest first, so it never receives the coursework boost.
        if exam_week:
            if _is_contest(it):
                score -= 4.0  # dial competitive practice below coursework
            elif _is_graded(it):
                score += 2.0  # focus the student on what's graded

        it.score = round(score, 2)
        it.priority = _to_priority(it.score)

    items.sort(key=lambda x: x.score, reverse=True)
    return items
