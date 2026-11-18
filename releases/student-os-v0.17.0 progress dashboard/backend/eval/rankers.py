"""Rankers under evaluation.

Each ranker maps an unordered list of ActionItems to a ranked list. The point
of the harness is to compare our prioritizer against simple, sensible baselines
so any improvement is measured, not asserted.
"""
from __future__ import annotations

import random
from datetime import date

from app.orchestrator.prioritizer import prioritize
from app.schemas import ActionItem

_FAR_FUTURE = "9999-12-31"


def source_order_ranker(items: list[ActionItem]) -> list[ActionItem]:
    """Baseline: whatever order the servers returned (no prioritization)."""
    return list(items)


def random_ranker(items: list[ActionItem], seed: int = 0) -> list[ActionItem]:
    """Baseline: random shuffle (the floor any real ranker must beat)."""
    out = list(items)
    random.Random(seed).shuffle(out)
    return out


def due_date_ranker(items: list[ActionItem]) -> list[ActionItem]:
    """Baseline: earliest due date first; undated items last. A strong, naive
    heuristic — beating it is the interesting result."""
    return sorted(items, key=lambda it: (it.due or _FAR_FUTURE)[:10])


def prioritizer_ranker(
    items: list[ActionItem], ref: date | None = None
) -> list[ActionItem]:
    """Our context-aware prioritizer (the treatment)."""
    return prioritize(list(items), ref=ref)


# Registry consumed by the runner. Add an LLM ranker here later behind a flag.
BASELINES = {
    "random": random_ranker,
    "source_order": source_order_ranker,
    "due_date": due_date_ranker,
}
