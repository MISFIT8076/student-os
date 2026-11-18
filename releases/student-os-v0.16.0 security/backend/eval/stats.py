"""Statistics for comparing two rankers across scenarios — dependency-free.

We use a paired design: each scenario yields one metric value per ranker, so
the natural comparison is a *paired* test on the per-scenario differences.

* Wilcoxon signed-rank test (non-parametric; doesn't assume normality) with
  tie + continuity correction and a normal approximation for the p-value.
* Percentile bootstrap confidence interval for the mean difference (an
  intuitive effect-size companion to the p-value).
* Rank-biserial effect size and win/tie/loss counts.

The implementations are validated against scipy in tests/test_stats.py.
"""
from __future__ import annotations

import math
import random
from collections import Counter
from collections.abc import Sequence


def _normal_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def _avg_ranks(values: list[float]) -> list[float]:
    """Ascending ranks with ties averaged (1-based)."""
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        avg = (i + 1 + j + 1) / 2.0  # average of positions i+1..j+1
        for k in range(i, j + 1):
            ranks[order[k]] = avg
        i = j + 1
    return ranks


def wilcoxon_signed_rank(diffs: Sequence[float]) -> dict:
    """Two-sided Wilcoxon signed-rank test on paired differences.

    Returns w_plus, w_minus, statistic (=min), z, p_value, n (nonzero pairs),
    and rank_biserial effect size. Zero differences are dropped (standard).
    """
    nonzero = [d for d in diffs if d != 0]
    n = len(nonzero)
    if n == 0:
        return {"w_plus": 0.0, "w_minus": 0.0, "statistic": 0.0, "z": 0.0,
                "p_value": 1.0, "n": 0, "rank_biserial": 0.0}

    abs_ranks = _avg_ranks([abs(d) for d in nonzero])
    w_plus = sum(r for d, r in zip(nonzero, abs_ranks) if d > 0)
    w_minus = sum(r for d, r in zip(nonzero, abs_ranks) if d < 0)
    total = w_plus + w_minus  # = n(n+1)/2

    mean_w = n * (n + 1) / 4.0
    var_w = n * (n + 1) * (2 * n + 1) / 24.0
    # Tie correction on |d| groups.
    tie_counts = Counter(abs(d) for d in nonzero)
    var_w -= sum(t ** 3 - t for t in tie_counts.values()) / 48.0

    if var_w <= 0:
        z = 0.0
    else:
        z = (abs(w_plus - mean_w) - 0.5) / math.sqrt(var_w)  # continuity correction
        z = max(z, 0.0)
    p = 2.0 * (1.0 - _normal_cdf(z))
    p = min(1.0, max(0.0, p))

    return {
        "w_plus": w_plus,
        "w_minus": w_minus,
        "statistic": min(w_plus, w_minus),
        "z": z,
        "p_value": p,
        "n": n,
        "rank_biserial": (w_plus - w_minus) / total if total else 0.0,
    }


def bootstrap_ci_mean(
    diffs: Sequence[float], iters: int = 10000, alpha: float = 0.05, seed: int = 0
) -> dict:
    """Percentile bootstrap CI for the mean of the differences."""
    diffs = list(diffs)
    if not diffs:
        return {"mean": 0.0, "low": 0.0, "high": 0.0}
    rng = random.Random(seed)
    n = len(diffs)
    means = []
    for _ in range(iters):
        sample = [diffs[rng.randrange(n)] for _ in range(n)]
        means.append(sum(sample) / n)
    means.sort()
    lo = means[int((alpha / 2) * iters)]
    hi = means[min(iters - 1, int((1 - alpha / 2) * iters))]
    return {"mean": sum(diffs) / n, "low": lo, "high": hi}


def win_tie_loss(a: Sequence[float], b: Sequence[float], tol: float = 1e-9) -> dict:
    """Count scenarios where a beats / ties / loses to b."""
    win = tie = loss = 0
    for x, y in zip(a, b):
        if x - y > tol:
            win += 1
        elif y - x > tol:
            loss += 1
        else:
            tie += 1
    return {"win": win, "tie": tie, "loss": loss}
