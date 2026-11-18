"""Independent audit of metric correctness for Student OS evaluation.

Re-implements all metrics from scratch and checks them against the repo's
eval/metrics.py and results.json. Also compares linear vs exponential nDCG gain.
"""
from __future__ import annotations

import json
import math
import zlib
import random
from pathlib import Path
from collections import Counter
from datetime import date, timedelta

from app.schemas import ActionItem
from app.orchestrator.prioritizer import prioritize
from eval.metrics import ndcg_at_k, precision_at_k, pairwise_accuracy, mrr
from eval.rankers import BASELINES

DATASET_PATH = Path("eval/dataset.json")
RESULTS_PATH = Path("eval/results.json")

def independent_dcg_linear(rels: list[float], k: int | None = None) -> float:
    if k is not None:
        rels = rels[:k]
    return sum(r / math.log2(idx + 1) for idx, r in enumerate(rels, start=1))

def independent_dcg_exponential(rels: list[float], k: int | None = None) -> float:
    if k is not None:
        rels = rels[:k]
    return sum((2.0**r - 1.0) / math.log2(idx + 1) for idx, r in enumerate(rels, start=1))

def independent_ndcg(rels: list[float], k: int, exponential: bool = False) -> float:
    dcg_fn = independent_dcg_exponential if exponential else independent_dcg_linear
    ideal = sorted(rels, reverse=True)
    idcg = dcg_fn(ideal, k)
    if idcg == 0.0:
        return 0.0
    return dcg_fn(rels, k) / idcg

def independent_precision_at_k(rels: list[float], k: int, threshold: float = 2.0) -> float:
    if k == 0:
        return 0.0
    topk = rels[:k]
    hits = sum(1 for r in topk if r >= threshold)
    return hits / k

def independent_pairwise_accuracy(rels: list[float]) -> float:
    concordant = 0
    discordant = 0
    n = len(rels)
    for i in range(n):
        for j in range(i + 1, n):
            if rels[i] > rels[j]:
                concordant += 1
            elif rels[i] < rels[j]:
                discordant += 1
    total = concordant + discordant
    return concordant / total if total > 0 else 1.0

def independent_mrr(rels: list[float], threshold: float = 3.0) -> float:
    for idx, r in enumerate(rels, start=1):
        if r >= threshold:
            return 1.0 / idx
    return 0.0

def build_items(scenario: dict, ref: date) -> list[ActionItem]:
    items: list[ActionItem] = []
    for it in scenario["items"]:
        offset = it.get("due_offset_days")
        due = (ref + timedelta(days=offset)).isoformat() if offset is not None else None
        raw = {"_gold": it["relevance"]}
        if "category" in it:
            raw["category"] = it["category"]
        items.append(
            ActionItem(
                source=it["source"],
                kind=it["kind"],
                title=it["title"],
                detail=it.get("detail", ""),
                due=due,
                raw=raw,
            )
        )
    seed = zlib.crc32(scenario["id"].encode())
    random.Random(seed).shuffle(items)
    return items

def main():
    print("=== INDEPENDENT METRIC CORRECTNESS AUDIT ===")
    data = json.loads(DATASET_PATH.read_text(encoding="utf-8"))
    scenarios = data["scenarios"]
    results = json.loads(RESULTS_PATH.read_text(encoding="utf-8"))
    per_scenario_repo = results["per_scenario"]

    # 1. Item counts
    item_counts = [len(s["items"]) for s in scenarios]
    count_dist = Counter(item_counts)
    print(f"Total scenarios: {len(scenarios)}")
    print(f"Item counts per scenario: min={min(item_counts)}, median={sorted(item_counts)[len(item_counts)//2]}, max={max(item_counts)}")
    print(f"Distribution of item counts: {dict(sorted(count_dist.items()))}")
    scenarios_le_5 = sum(1 for c in item_counts if c <= 5)
    print(f"Scenarios with <= 5 items: {scenarios_le_5} / {len(scenarios)} ({scenarios_le_5/len(scenarios):.1%})")

    # 2. Grade 3 check
    grade_counts = Counter()
    scenarios_without_grade3 = []
    for s in scenarios:
        grades = [it["relevance"] for it in s["items"]]
        for g in grades:
            grade_counts[g] += 1
        if 3 not in grades:
            scenarios_without_grade3.append(s["id"])
    print(f"\nOverall grade counts: {dict(sorted(grade_counts.items()))}")
    print(f"Scenarios without any grade-3 item: {len(scenarios_without_grade3)} -> {scenarios_without_grade3}")

    # 3. Verify per-scenario values against repo output
    ref = date.today()
    mismatches = 0
    checks = 0

    exp_ndcg3 = {r: [] for r in ["random", "source_order", "due_date", "prioritizer"]}
    exp_ndcg5 = {r: [] for r in ["random", "source_order", "due_date", "prioritizer"]}
    lin_ndcg3 = {r: [] for r in ["random", "source_order", "due_date", "prioritizer"]}
    lin_ndcg5 = {r: [] for r in ["random", "source_order", "due_date", "prioritizer"]}

    for sc in scenarios:
        sid = sc["id"]
        items = build_items(sc, ref)
        repo_sc = per_scenario_repo[sid]

        for rname in ["source_order", "due_date", "prioritizer"]:
            if rname == "prioritizer":
                ranked = prioritize(list(items), ref=ref)
            else:
                ranked = BASELINES[rname](items)
            rels = [float(x.raw["_gold"]) for x in ranked]

            n3 = independent_ndcg(rels, 3, exponential=False)
            n5 = independent_ndcg(rels, 5, exponential=False)
            p3 = independent_precision_at_k(rels, 3)
            pw = independent_pairwise_accuracy(rels)
            m = independent_mrr(rels)

            lin_ndcg3[rname].append(n3)
            lin_ndcg5[rname].append(n5)
            exp_ndcg3[rname].append(independent_ndcg(rels, 3, exponential=True))
            exp_ndcg5[rname].append(independent_ndcg(rels, 5, exponential=True))

            repo_vals = repo_sc[rname]
            for metric_name, my_val, repo_val in [
                ("nDCG@3", n3, repo_vals["nDCG@3"]),
                ("nDCG@5", n5, repo_vals["nDCG@5"]),
                ("P@3", p3, repo_vals["P@3"]),
                ("pairwise", pw, repo_vals["pairwise"]),
                ("MRR", m, repo_vals["MRR"]),
            ]:
                checks += 1
                if abs(my_val - repo_val) > 1e-6:
                    print(f"MISMATCH in {sid} {rname} {metric_name}: independent={my_val:.6f}, repo={repo_val:.6f}")
                    mismatches += 1

    print(f"\nVerification of metric implementation across scenarios: {checks} checks, {mismatches} mismatches.")
    if mismatches == 0:
        print("VERIFIED: Repo metric code matches independent re-implementation perfectly!")

    # 4. Compare Linear vs Exponential nDCG means
    print("\n--- GAIN FUNCTION COMPARISON: LINEAR (repo) vs EXPONENTIAL (standard 2^rel - 1) ---")
    print(f"{'Ranker':<15} | {'Linear nDCG@3':<14} | {'Exp nDCG@3':<12} | {'Linear nDCG@5':<14} | {'Exp nDCG@5':<12}")
    print("-" * 75)
    for r in ["source_order", "due_date", "prioritizer"]:
        l3 = sum(lin_ndcg3[r]) / len(lin_ndcg3[r])
        e3 = sum(exp_ndcg3[r]) / len(exp_ndcg3[r])
        l5 = sum(lin_ndcg5[r]) / len(lin_ndcg5[r])
        e5 = sum(exp_ndcg5[r]) / len(exp_ndcg5[r])
        print(f"{r:<15} | {l3:<14.3f} | {e3:<12.3f} | {l5:<14.3f} | {e5:<12.3f}")

    prio_due_delta_lin = (sum(lin_ndcg5["prioritizer"]) - sum(lin_ndcg5["due_date"])) / 40.0
    prio_due_delta_exp = (sum(exp_ndcg5["prioritizer"]) - sum(exp_ndcg5["due_date"])) / 40.0
    print(f"\nprioritizer vs due_date delta on nDCG@5:")
    print(f"  Linear gain (reported in paper):      +{prio_due_delta_lin:.3f}")
    print(f"  Exponential gain (2^rel - 1):         +{prio_due_delta_exp:.3f}")

if __name__ == "__main__":
    main()
