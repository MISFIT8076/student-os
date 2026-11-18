"""Ranking-quality metrics.

Each metric takes the predicted ranking expressed as the list of *gold
relevance grades* in predicted order. Relevance is graded 0-3:

    3 = must do today   2 = important soon   1 = optional   0 = noise

Example: if the ranker puts items with gold grades [3, 1, 2, 0] in that order,
you pass [3, 1, 2, 0].

Kept dependency-free and explicit so the formulas can be cited in the report.
"""
from __future__ import annotations

import math
from collections.abc import Sequence


def dcg(relevances: Sequence[float], k: int | None = None) -> float:
    """Discounted Cumulative Gain: sum rel_i / log2(i + 1), i starting at 1."""
    if k is not None:
        relevances = relevances[:k]
    return sum(rel / math.log2(i + 2) for i, rel in enumerate(relevances))


def ndcg_at_k(predicted_relevances: Sequence[float], k: int) -> float:
    """Normalized DCG@k in [0, 1]. 1.0 = ideal ordering. 0 if no relevance."""
    ideal = sorted(predicted_relevances, reverse=True)
    idcg = dcg(ideal, k)
    if idcg == 0:
        return 0.0
    return dcg(predicted_relevances, k) / idcg


def precision_at_k(
    predicted_relevances: Sequence[float], k: int, threshold: float = 2.0
) -> float:
    """Fraction of the top-k that are 'relevant' (grade >= threshold)."""
    if k == 0:
        return 0.0
    topk = predicted_relevances[:k]
    hits = sum(1 for r in topk if r >= threshold)
    return hits / k


def pairwise_accuracy(predicted_relevances: Sequence[float]) -> float:
    """Fraction of gold-ordered pairs the ranking gets right (ties excluded).

    For every pair (i < j) in predicted order, the pair is concordant if the
    earlier item has strictly higher gold relevance. Equal-relevance pairs are
    ignored. Equivalent to (Kendall's tau + 1) / 2 over untied pairs. Reversed
    ranking -> 0.0, perfect -> 1.0.
    """
    concordant = discordant = 0
    n = len(predicted_relevances)
    for i in range(n):
        for j in range(i + 1, n):
            a, b = predicted_relevances[i], predicted_relevances[j]
            if a > b:
                concordant += 1
            elif a < b:
                discordant += 1
    total = concordant + discordant
    return concordant / total if total else 1.0


def mrr(predicted_relevances: Sequence[float], threshold: float = 3.0) -> float:
    """Mean Reciprocal Rank of the first item with grade >= threshold."""
    for i, rel in enumerate(predicted_relevances, start=1):
        if rel >= threshold:
            return 1.0 / i
    return 0.0
