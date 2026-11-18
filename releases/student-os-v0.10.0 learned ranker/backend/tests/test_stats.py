"""Tests for the significance helpers, including a cross-check against scipy
(skipped automatically if scipy isn't installed — it is NOT a project runtime
dependency)."""
from __future__ import annotations

import pytest

from eval.stats import bootstrap_ci_mean, wilcoxon_signed_rank, win_tie_loss

# A vector with zeros (dropped) and ties (0.1 repeated) to exercise corrections.
DIFFS = [0.0, 0.1, 0.1, -0.05, 0.2, 0.0, 0.15, -0.1, 0.1, 0.3, 0.0, 0.05]


def test_wilcoxon_drops_zero_diffs():
    r = wilcoxon_signed_rank(DIFFS)
    assert r["n"] == 9  # 12 values, 3 are exactly 0.0 and are dropped


def test_wilcoxon_all_zero_is_p_one():
    r = wilcoxon_signed_rank([0.0, 0.0, 0.0])
    assert r["n"] == 0 and r["p_value"] == 1.0


def test_wilcoxon_strong_effect_is_significant():
    r = wilcoxon_signed_rank([0.2] * 12)  # all positive -> should be significant
    assert r["p_value"] < 0.05
    assert r["rank_biserial"] == pytest.approx(1.0)


def test_wilcoxon_symmetric_not_significant():
    r = wilcoxon_signed_rank([0.1, -0.1, 0.1, -0.1, 0.1, -0.1])
    assert r["p_value"] > 0.5


def test_bootstrap_ci_contains_mean_and_is_ordered():
    ci = bootstrap_ci_mean(DIFFS, iters=2000, seed=1)
    assert ci["low"] <= ci["mean"] <= ci["high"]


def test_bootstrap_ci_constant_is_degenerate():
    ci = bootstrap_ci_mean([0.2, 0.2, 0.2], iters=500, seed=1)
    assert ci["low"] == ci["high"] == pytest.approx(0.2)


def test_win_tie_loss_counts():
    a = [0.9, 0.5, 0.7]
    b = [0.8, 0.5, 0.9]
    assert win_tie_loss(a, b) == {"win": 1, "tie": 1, "loss": 1}


def test_matches_scipy_within_tolerance():
    scipy_stats = pytest.importorskip("scipy.stats")
    try:
        res = scipy_stats.wilcoxon(DIFFS, correction=True, method="approx",
                                   zero_method="wilcox")
    except TypeError:  # older scipy uses `mode` instead of `method`
        res = scipy_stats.wilcoxon(DIFFS, correction=True, mode="approx",
                                   zero_method="wilcox")
    ours = wilcoxon_signed_rank(DIFFS)
    assert ours["p_value"] == pytest.approx(res.pvalue, abs=0.02)
