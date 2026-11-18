"""Unit tests for the ranking metrics — the result is only as trustworthy as
these formulas, so pin them down."""
from __future__ import annotations

import math

from eval.metrics import mrr, ndcg_at_k, pairwise_accuracy, precision_at_k


def test_ndcg_perfect_is_one():
    assert ndcg_at_k([3, 2, 1, 0], 4) == 1.0


def test_ndcg_reversed_is_less_than_perfect():
    assert ndcg_at_k([0, 1, 2, 3], 4) < 1.0


def test_ndcg_all_zero_is_one():
    assert ndcg_at_k([0, 0, 0], 3) == 1.0


def test_ndcg_known_value():
    # order [2, 3]: DCG = 2/log2(2) + 3/log2(3); IDCG (ideal [3,2]) = 3 + 2/log2(3)
    dcg = 2 / math.log2(2) + 3 / math.log2(3)
    idcg = 3 / math.log2(2) + 2 / math.log2(3)
    assert math.isclose(ndcg_at_k([2, 3], 2), dcg / idcg)


def test_precision_at_k():
    assert precision_at_k([3, 2, 1, 0], 2, threshold=2.0) == 1.0
    assert math.isclose(precision_at_k([3, 2, 1, 0], 3, threshold=2.0), 2 / 3)
    assert precision_at_k([1, 1, 0], 3, threshold=2.0) == 0.0


def test_pairwise_accuracy():
    assert pairwise_accuracy([3, 2, 1, 0]) == 1.0
    assert pairwise_accuracy([0, 1, 2, 3]) == 0.0
    assert pairwise_accuracy([2, 2]) == 1.0  # ties excluded -> no discordant pairs


def test_mrr():
    assert mrr([3, 2, 1], threshold=3.0) == 1.0
    assert mrr([1, 3], threshold=3.0) == 0.5
    assert mrr([1, 1], threshold=3.0) == 0.0


def test_oracle_ndcg_all_splits():
    import json
    from pathlib import Path
    data_dir = Path("C:/Users/aggar/internship/research/evidence/data")
    if not data_dir.exists():
        return
    for split in ["dev", "test_heldout", "test_long", "test_perturbed"]:
        split_path = data_dir / f"{split}.json"
        if not split_path.exists():
            continue
        data = json.loads(split_path.read_text(encoding="utf-8"))
        for sc in data["scenarios"]:
            rels = [float(it["relevance"]) for it in sc["items"]]
            oracle_rels = sorted(rels, reverse=True)
            for k in [3, 5, 10]:
                score = ndcg_at_k(oracle_rels, k)
                assert math.isclose(score, 1.0, rel_tol=1e-7), f"Failed on {split}:{sc['id']} at k={k}, got {score}"

