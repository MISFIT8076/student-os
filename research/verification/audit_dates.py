"""Audit of date sensitivity for Student OS evaluation.

Tests whether running eval.run_eval with different reference dates
(e.g. Monday, Saturday, month-end, leap year, DST change) affects the metrics.
"""
from __future__ import annotations

import json
import statistics
import zlib
from datetime import date, timedelta
from pathlib import Path

from app.orchestrator.prioritizer import prioritize
from app.schemas import ActionItem
from eval.metrics import ndcg_at_k
from eval.rankers import BASELINES

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
    import random
    random.Random(seed).shuffle(items)
    return items

def main():
    print("=== DATE SENSITIVITY AUDIT ===")
    data = json.loads(DATASET_PATH.read_text(encoding="utf-8"))
    scenarios = data["scenarios"]

    test_dates = [
        ("Default (today)", date.today()),
        ("A Monday", date(2026, 8, 3)),
        ("A Wednesday", date(2026, 8, 5)),
        ("A Saturday", date(2026, 8, 8)),
        ("A Sunday", date(2026, 8, 9)),
        ("Month end (31st)", date(2026, 8, 31)),
        ("Leap day", date(2028, 2, 29)),
        ("Near DST change", date(2026, 10, 25)),
    ]

    print(f"{'Date description':<22} | {'Date ISO':<10} | {'due_date nDCG@5':<16} | {'prioritizer nDCG@5':<18} | {'Delta':<8}")
    print("-" * 85)

    base_prio = None
    base_due = None
    all_identical = True

    for desc, test_dt in test_dates:
        prio_scores = []
        due_scores = []
        for sc in scenarios:
            items = build_items(sc, test_dt)
            p_ranked = prioritize(list(items), ref=test_dt)
            d_ranked = BASELINES["due_date"](items)

            p_n5 = ndcg_at_k([float(x.raw["_gold"]) for x in p_ranked], 5)
            d_n5 = ndcg_at_k([float(x.raw["_gold"]) for x in d_ranked], 5)
            prio_scores.append(p_n5)
            due_scores.append(d_n5)

        m_prio = statistics.mean(prio_scores)
        m_due = statistics.mean(due_scores)
        delta = m_prio - m_due
        print(f"{desc:<22} | {test_dt.isoformat():<10} | {m_due:<16.6f} | {m_prio:<18.6f} | {delta:<+8.6f}")

        if base_prio is None:
            base_prio = m_prio
            base_due = m_due
        else:
            if abs(m_prio - base_prio) > 1e-9 or abs(m_due - base_due) > 1e-9:
                all_identical = False

    print(f"\nDate sensitivity verdict: {'COMPLETELY DATE-INVARIANT (0.000000 drift across all dates)' if all_identical else 'DATE SENSITIVE'}")
    print("Reason: The evaluation dataset stores deadlines as integer offsets (due_offset_days).")
    print("Prioritizer and due_date rankers only inspect day differences ((d - ref).days), which exactly equals the integer offset regardless of what day of the week or year ref falls on.")

if __name__ == "__main__":
    main()
