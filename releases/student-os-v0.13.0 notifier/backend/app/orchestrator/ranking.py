"""Ranker selection.

Returns (name, rank_fn) based on config. RANKER=learned uses the trained model
when available and otherwise transparently falls back to the rule-based
prioritizer — so the app always ranks, even before any model is trained.
"""
from __future__ import annotations

from datetime import date
from typing import Callable

from app.config import get_settings
from app.orchestrator.prioritizer import prioritize
from app.schemas import ActionItem

Ranker = Callable[[list[ActionItem]], list[ActionItem]]


def get_ranker() -> tuple[str, Ranker]:
    if get_settings().ranker == "learned":
        try:
            from app.intelligence.learned_ranker import LearnedRanker

            lr = LearnedRanker()
            if lr.available():
                return "learned", lambda items: lr.rank(items, date.today())
        except Exception:  # noqa: BLE001 — any issue → safe fallback
            pass
    return "rule", lambda items: prioritize(items, ref=date.today())
