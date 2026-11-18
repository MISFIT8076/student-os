"""Audit of dataset validity, taxonomy, balance, and label noise sensitivity.

Examines:
1. Scenario taxonomy and breakdown.
2. In how many scenarios due_date is already optimal.
3. Label distribution per scenario.
4. Single-annotator fragility: simulate 10% and 20% label noise over 1,000 Monte Carlo trials
   and report how often prioritizer still significantly beats due_date (p < 0.05).
"""
from __future__ import annotations

import json
import random
import statistics
import zlib
from datetime import date, timedelta
from pathlib import Path
from collections import Counter

from app.orchestrator.prioritizer import prioritize
from app.schemas import ActionItem
from eval.metrics import ndcg_at_k
from eval.rankers import BASELINES
from eval.stats import wilcoxon_signed_rank

DATASET_PATH = Path("eval/dataset.json")

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

def categorize_scenario(sid: str) -> str:
    s = sid.lower()
    if "exam" in s or "prep" in s:
        return "exam_prep"
    if "placement" in s or "internship" in s or "recruit" in s or "interview" in s:
        return "placement_internship"
    if "deadline" in s or "cluster" in s or "crunch" in s:
        return "deadline_cluster"
    if "contest" in s or "codeforces" in s or "hackathon" in s:
        return "contest_hackathon"
    if "noise" in s or "quiet" in s or "relief" in s or "winddown" in s or "nothing" in s:
        return "quiet_or_noise"
    return "general_student_life"

def main():
    print("=== DATASET VALIDITY AND NOISE ROBUSTNESS AUDIT ===")
    data = json.loads(DATASET_PATH.read_text(encoding="utf-8"))
    scenarios = data["scenarios"]
    ref = date.today()

    # 1. Taxonomy
    taxonomy = Counter(categorize_scenario(sc["id"]) for sc in scenarios)
    print("\n--- 1. SCENARIO TAXONOMY ---")
    for cat, cnt in taxonomy.most_common():
        print(f"  {cat:<25}: {cnt:2d} scenarios ({cnt/len(scenarios):.1%})")

    # 2. Per-category performance
    cat_scenarios = {}
    for sc in scenarios:
        cat = categorize_scenario(sc["id"])
        cat_scenarios.setdefault(cat, []).append(sc)

    print("\n--- 2. PER-CATEGORY METRICS (nDCG@5) ---")
    print(f"{'Category':<25} | {'N':<3} | {'due_date':<9} | {'prioritizer':<12} | {'Delta':<8} | {'Win/Tie/Loss'}")
    print("-" * 80)
    for cat, sc_list in cat_scenarios.items():
        due_scores = []
        prio_scores = []
        w = t = l = 0
        for sc in sc_list:
            items = build_items(sc, ref)
            d_rel = [float(x.raw["_gold"]) for x in BASELINES["due_date"](items)]
            p_rel = [float(x.raw["_gold"]) for x in prioritize(list(items), ref=ref)]
            d_n5 = ndcg_at_k(d_rel, 5)
            p_n5 = ndcg_at_k(p_rel, 5)
            due_scores.append(d_n5)
            prio_scores.append(p_n5)
            if p_n5 - d_n5 > 1e-6:
                w += 1
            elif d_n5 - p_n5 > 1e-6:
                l += 1
            else:
                t += 1
        m_due = statistics.mean(due_scores)
        m_prio = statistics.mean(prio_scores)
        print(f"{cat:<25} | {len(sc_list):<3} | {m_due:<9.3f} | {m_prio:<12.3f} | {m_prio - m_due:<+8.3f} | {w}/{t}/{l}")

    # 3. Check "due_date optimal" claim
    due_date_optimal = 0
    prio_optimal = 0
    for sc in scenarios:
        items = build_items(sc, ref)
        d_rel = [float(x.raw["_gold"]) for x in BASELINES["due_date"](items)]
        p_rel = [float(x.raw["_gold"]) for x in prioritize(list(items), ref=ref)]
        if abs(ndcg_at_k(d_rel, 5) - 1.0) < 1e-6:
            due_date_optimal += 1
        if abs(ndcg_at_k(p_rel, 5) - 1.0) < 1e-6:
            prio_optimal += 1

    print(f"\nOptimal nDCG@5 (1.000):")
    print(f"  due_date is optimal in:    {due_date_optimal} / 40 scenarios ({due_date_optimal/40:.1%})")
    print(f"  prioritizer is optimal in: {prio_optimal} / 40 scenarios ({prio_optimal/40:.1%})")

    # 4. Monte Carlo label noise simulation (1,000 trials)
    print("\n--- 3. LABEL NOISE ROBUSTNESS SIMULATION (1,000 TRIALS) ---")
    for noise_rate in [0.10, 0.20]:
        sig_count = 0
        p_wins = 0
        deltas = []
        trials = 1000
        rng = random.Random(1337 + int(noise_rate * 100))

        for _ in range(trials):
            trial_prio_n5 = []
            trial_due_n5 = []

            for sc in scenarios:
                items = build_items(sc, ref)
                # Perturb labels
                noisy_items = []
                for it in items:
                    g = int(it.raw["_gold"])
                    if rng.random() < noise_rate:
                        shift = rng.choice([-1, 1])
                        g = max(0, min(3, g + shift))
                    noisy_it = ActionItem(
                        source=it.source,
                        kind=it.kind,
                        title=it.title,
                        detail=it.detail,
                        due=it.due,
                        raw={"_gold": g, "category": it.raw.get("category")},
                    )
                    noisy_items.append(noisy_it)

                p_ranked = prioritize(list(noisy_items), ref=ref)
                d_ranked = BASELINES["due_date"](noisy_items)

                p_rel = [float(x.raw["_gold"]) for x in p_ranked]
                d_rel = [float(x.raw["_gold"]) for x in d_ranked]

                trial_prio_n5.append(ndcg_at_k(p_rel, 5))
                trial_due_n5.append(ndcg_at_k(d_rel, 5))

            diffs = [p - d for p, d in zip(trial_prio_n5, trial_due_n5)]
            mean_d = statistics.mean(diffs)
            deltas.append(mean_d)
            if mean_d > 0:
                p_wins += 1
            w_res = wilcoxon_signed_rank(diffs)
            if w_res["p_value"] < 0.05 and mean_d > 0:
                sig_count += 1

        print(f"Noise rate {noise_rate:.0%}:")
        print(f"  Mean delta across 1000 trials: {statistics.mean(deltas):+.4f} (std={statistics.stdev(deltas):.4f})")
        print(f"  Prioritizer has positive delta in: {p_wins} / {trials} trials ({p_wins/trials:.1%})")
        print(f"  Prioritizer significantly beats due_date (p < 0.05) in: {sig_count} / {trials} trials ({sig_count/trials:.1%})")

if __name__ == "__main__":
    main()
