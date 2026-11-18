"""Opportunity radar — surface and track internships, scholarships,
hackathons, and contests in one place.

Classifies gathered items into opportunity types and merges in the student's
application status (interested / applied / rejected / offer), which is persisted
in the store. This is the placement-season feature: the things most costly to
miss, tracked from spotted → applied → outcome.
"""
from __future__ import annotations

from app import store
from app.schemas import ActionItem

_INTERNSHIP = ("intern", "internship", "recruiter", "placement", "sde", "hiring", "job")
_SCHOLARSHIP = ("scholarship", "fellowship", "grant", "stipend")
_HACKATHON = ("hackathon", "hack ")
_CONTEST = ("contest", "codeforces", "leetcode", "round", "coding challenge")


def classify_opportunity(item: ActionItem) -> str | None:
    text = f"{item.title} {item.detail}".lower()
    category = str(item.raw.get("category", "")).lower()

    if any(k in text for k in _HACKATHON):
        return "hackathon"
    if any(k in text for k in _SCHOLARSHIP):
        return "scholarship"
    if category == "internship" or any(k in text for k in _INTERNSHIP):
        return "internship"
    if item.kind == "contest" or item.source == "codeforces" or any(k in text for k in _CONTEST):
        return "contest"
    return None


def collect_opportunities(items: list[ActionItem]) -> list[dict]:
    """Return classified opportunities merged with saved application status."""
    statuses = store.get_opportunity_statuses()
    out: list[dict] = []
    for it in items:
        otype = classify_opportunity(it)
        if otype is None:
            continue
        key = store.item_key(it.source, it.title, it.due)
        out.append({
            "key": key,
            "type": otype,
            "title": it.title,
            "detail": it.detail,
            "source": it.source,
            "kind": it.kind,
            "due": it.due,
            "url": it.url,
            "status": statuses.get(key, "new"),
        })
    # Soonest deadlines first, undated last.
    out.sort(key=lambda o: (o["due"] or "9999-12-31"))
    return out
