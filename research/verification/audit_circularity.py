"""Circularity, test-set overfitting, and keyword overlap audit.

Examines:
1. Every keyword, kind, category, and threshold in prioritizer.py.
2. How many times each fires across the 40 scenarios.
3. Whether rules fire only on specific benchmark scenarios (overfitting / tailored rules).
4. Training data contamination for LearnedRanker.
"""
from __future__ import annotations

import json
from pathlib import Path
from collections import Counter

DATASET_PATH = Path("eval/dataset.json")

def main():
    print("=== CIRCULARITY AND OVERFITTING AUDIT ===")
    data = json.loads(DATASET_PATH.read_text(encoding="utf-8"))
    scenarios = data["scenarios"]

    # All items across all 40 scenarios
    all_items = []
    for sc in scenarios:
        for it in sc["items"]:
            all_items.append((sc["id"], it))

    total_items = len(all_items)
    print(f"Total action items across 40 scenarios: {total_items}")

    # 1. Kinds frequency
    kinds = Counter(it["kind"] for _, it in all_items)
    print(f"\nItem kind distribution in dataset:")
    for k, v in kinds.most_common():
        print(f"  {k:<15}: {v:2d} ({v/total_items:.1%})")

    # 2. Email categories
    email_items = [it for _, it in all_items if it["kind"] == "email"]
    email_cats = Counter(it.get("category", "none") for it in email_items)
    print(f"\nEmail categories (total emails = {len(email_items)}):")
    for cat, v in email_cats.most_common():
        print(f"  {cat:<15}: {v:2d} ({v/len(email_items):.1%})")

    # 3. Contest hints keyword analysis
    # _CONTEST_HINTS = ("contest", "codeforces", "leetcode", "hackathon", "round")
    hints = ("contest", "codeforces", "leetcode", "hackathon", "round")
    print(f"\nContest hint keyword appearances:")
    hint_matches = {h: [] for h in hints}
    for sid, it in all_items:
        text = f"{it['title']} {it.get('detail', '')}".lower()
        for h in hints:
            if h in text:
                hint_matches[h].append((sid, it["title"]))

    for h, matches in hint_matches.items():
        print(f"  '{h}': {len(matches)} occurrences")
        # List unique titles
        unique_titles = set(t for _, t in matches)
        for t in list(unique_titles)[:3]:
            print(f"      e.g.: '{t}'")

    # 4. Exam week trigger analysis
    # _exam_week: any item with kind == 'exam' and 0 <= due_offset_days <= 5
    exam_week_scenarios = []
    for sc in scenarios:
        has_exam_week = False
        for it in sc["items"]:
            if it["kind"] == "exam":
                off = it.get("due_offset_days")
                if off is not None and 0 <= off <= 5:
                    has_exam_week = True
                    break
        if has_exam_week:
            exam_week_scenarios.append(sc["id"])

    print(f"\nExam week triggered in: {len(exam_week_scenarios)} / {len(scenarios)} scenarios ({len(exam_week_scenarios)/len(scenarios):.1%})")
    print(f"Scenarios: {exam_week_scenarios}")

    # 5. Check if any rules fire 0 times in dataset
    # Prioritizer kind weights:
    prioritizer_kinds = ["exam", "deadline", "pull_request", "contest", "notification", "issue", "email", "practice", "announcement", "event", "error"]
    unused_kinds = [k for k in prioritizer_kinds if k not in kinds]
    print(f"\nPrioritizer kinds that NEVER appear in benchmark: {unused_kinds}")

    # Prioritizer email categories:
    prio_cats = ["internship", "academic", "otp"]
    unused_cats = [c for c in prio_cats if c not in email_cats]
    print(f"Prioritizer email categories that NEVER appear in benchmark: {unused_cats}")

    # 6. Check circularity:
    print("\n--- CIRCULARITY & AUTHORSHIP COUPLING FINDINGS ---")
    print("CRITICAL FINDING: The prioritizer's rule set and the benchmark scenarios have tight coupling:")
    print("1. All 3 email category bonuses in prioritizer.py ('internship': +4, 'academic': +2, 'otp': -3) map 1-to-1 to the 3 explicit categories authored in build_dataset.py.")
    print("2. The keyword list _CONTEST_HINTS ('contest', 'codeforces', 'leetcode', 'hackathon', 'round') in prioritizer.py matches the exact tokens authored in contest titles.")
    print("3. Single author wrote both prioritizer.py and build_dataset.py. While relevance grades are integer literals rather than computed, the rules were designed with these exact 40 scenarios in mind.")
    print("4. LearnedRanker training contamination: app/intelligence/train.py trains on all 40 scenarios in dataset.json, and saves ranker_weights.json. While eval/run_eval.py runs LOSO for the reported metrics, the deployed model weights are 100% trained on the test set.")

if __name__ == "__main__":
    main()
