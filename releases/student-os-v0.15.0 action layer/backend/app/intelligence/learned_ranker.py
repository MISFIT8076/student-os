"""Runtime learned ranker.

Loads the weights trained by `app.intelligence.train` and ranks live
ActionItems by predicted relevance. If no trained weights exist yet, it reports
itself unavailable so the caller can fall back to the rule-based prioritizer
(cold start). Same feature code as training, so there's no train/serve skew.
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from app.intelligence.features import FEATURE_NAMES, featurize, vectorize
from app.orchestrator.prioritizer import _days_until, _exam_week
from app.schemas import ActionItem, Priority

WEIGHTS = Path(__file__).resolve().parent / "ranker_weights.json"


def _to_priority(score: float) -> Priority:
    if score >= 2.5:
        return Priority.urgent
    if score >= 1.5:
        return Priority.high
    if score >= 0.75:
        return Priority.medium
    return Priority.low


class LearnedRanker:
    def __init__(self) -> None:
        self._w: list[float] | None = None
        self._b: float = 0.0
        self._names: list[str] = []
        if WEIGHTS.exists():
            data = json.loads(WEIGHTS.read_text())
            self._w = data["weights"]
            self._b = data["bias"]
            self._names = data["feature_names"]

    def available(self) -> bool:
        # Guard against a stale model trained on a different feature set.
        return self._w is not None and self._names == FEATURE_NAMES

    def _score(self, feats: dict[str, float]) -> float:
        vec = vectorize(feats)
        return sum(wi * xi for wi, xi in zip(self._w, vec)) + self._b

    def rank(self, items: list[ActionItem], ref: date | None = None) -> list[ActionItem]:
        ref = ref or date.today()
        exam_week = _exam_week(items, ref)
        for it in items:
            feats = featurize(
                source=it.source,
                kind=it.kind,
                days_until=_days_until(it.due, ref),
                category=str(it.raw.get("category")) if it.raw.get("category") else None,
                title=it.title,
                detail=it.detail,
                exam_week=exam_week,
            )
            it.score = round(self._score(feats), 3)
            it.priority = _to_priority(it.score)
        items.sort(key=lambda x: x.score, reverse=True)
        return items
