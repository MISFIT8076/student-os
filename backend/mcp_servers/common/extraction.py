"""Deadline extraction from unstructured text.

Emails and announcements hide deadlines in prose ("apply by Friday", "submit
before 3 August", "closes in 2 days"). This turns that text into a concrete due
date so such items can be ranked and scheduled like calendar deadlines.

Dependency-free and deterministic (pure `re` + `datetime`) so it's easy to
unit-test and explain in the report. Handles relative dates (today/tomorrow/
day-after/weekdays/"in N days") and absolute dates ("3 August", "Aug 3",
"3/8", "03-08-2026"). Returns the earliest plausible future date.
"""
from __future__ import annotations

import re
from datetime import date, timedelta

_MONTHS = {
    "jan": 1, "january": 1, "feb": 2, "february": 2, "mar": 3, "march": 3,
    "apr": 4, "april": 4, "may": 5, "jun": 6, "june": 6, "jul": 7, "july": 7,
    "aug": 8, "august": 8, "sep": 9, "sept": 9, "september": 9, "oct": 10,
    "october": 10, "nov": 11, "november": 11, "dec": 12, "december": 12,
}
_WEEKDAYS = {
    "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
    "friday": 4, "saturday": 5, "sunday": 6,
}
# Words that signal a deadline is being stated (raises confidence).
_TRIGGERS = (
    "by", "before", "due", "deadline", "submit", "apply", "closes", "closing",
    "last date", "register", "registration", "rsvp", "ends", "expires",
)

_MONTH_ALT = "|".join(sorted(_MONTHS, key=len, reverse=True))


def _next_weekday(ref: date, target: int) -> date:
    return ref + timedelta(days=(target - ref.weekday()) % 7)


def _roll_future(d: date, ref: date) -> date:
    """If a month/day date already passed this year, roll to next year."""
    if d < ref:
        try:
            return d.replace(year=d.year + 1)
        except ValueError:
            return d
    return d


def _candidates(text: str, ref: date) -> list[date]:
    t = text.lower()
    out: list[date] = []

    if "day after tomorrow" in t:
        out.append(ref + timedelta(days=2))
        t = t.replace("day after tomorrow", " ")  # so it isn't re-matched as "tomorrow"
    if re.search(r"\btomorrow\b", t):
        out.append(ref + timedelta(days=1))
    if re.search(r"\b(today|tonight)\b", t):
        out.append(ref)

    m = re.search(r"\bin (\d{1,2}) days?\b", t)
    if m:
        out.append(ref + timedelta(days=int(m.group(1))))

    for name, idx in _WEEKDAYS.items():
        if re.search(rf"\b{name}\b", t):
            out.append(_next_weekday(ref, idx))

    # "3 August" / "3rd august"
    for m in re.finditer(rf"\b(\d{{1,2}})(?:st|nd|rd|th)?\s+({_MONTH_ALT})\b", t):
        day, mon = int(m.group(1)), _MONTHS[m.group(2)]
        out.append(_safe_date(ref.year, mon, day, ref))
    # "August 3" / "aug 3rd"
    for m in re.finditer(rf"\b({_MONTH_ALT})\s+(\d{{1,2}})(?:st|nd|rd|th)?\b", t):
        mon, day = _MONTHS[m.group(1)], int(m.group(2))
        out.append(_safe_date(ref.year, mon, day, ref))

    # Numeric d/m or d-m (day-first; optional year). Skip pure times like 10:30.
    for m in re.finditer(r"\b(\d{1,2})[/-](\d{1,2})(?:[/-](\d{2,4}))?\b", t):
        day, mon = int(m.group(1)), int(m.group(2))
        if day > 31 or mon == 0:
            continue
        if mon > 12:  # looks like month/day; swap
            day, mon = mon, day
        if mon > 12:
            continue
        year = m.group(3)
        if year:
            y = int(year)
            y += 2000 if y < 100 else 0
            out.append(_safe_date(y, mon, day, ref, roll=False))
        else:
            out.append(_safe_date(ref.year, mon, day, ref))

    return [d for d in out if d is not None]


def _safe_date(year: int, month: int, day: int, ref: date, roll: bool = True):
    try:
        d = date(year, month, day)
    except ValueError:
        return None
    return _roll_future(d, ref) if roll else d


def has_trigger(text: str) -> bool:
    return any(trig in text.lower() for trig in _TRIGGERS)


def extract_due(text: str, ref: date | None = None) -> str | None:
    """Return the earliest plausible future due date (ISO) found in text, or None."""
    ref = ref or date.today()
    cands = [d for d in _candidates(text, ref) if d >= ref]
    if not cands:
        return None
    return min(cands).isoformat()


def enrich_due(items: list[dict], ref: date | None = None) -> list[dict]:
    """Fill in `due` for items that lack one, from their title/detail text.

    Marks extra['due_source']='extracted' so the UI/report can distinguish
    extracted deadlines from calendar-sourced ones.
    """
    ref = ref or date.today()
    for it in items:
        if it.get("due"):
            continue
        text = f"{it.get('title', '')} {it.get('detail', '')}"
        due = extract_due(text, ref)
        if due:
            it["due"] = due
            it.setdefault("extra", {})["due_source"] = "extracted"
    return items
