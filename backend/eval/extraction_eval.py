"""Evaluate deadline extraction: precision / recall / F1 on the labeled set.

    cd backend && python -m eval.extraction_eval
"""
from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path

from mcp_servers.common.extraction import extract_due

DATASET = Path(__file__).resolve().parent / "extraction_dataset.json"


def run() -> dict:
    data = json.loads(DATASET.read_text())
    ref = date.fromisoformat(data["reference_date"])
    tp = fp = fn = tn = 0
    wrong = []
    for ex in data["examples"]:
        pred = extract_due(ex["text"], ref)
        off = ex["expect_offset_days"]
        expected = (ref + timedelta(days=off)).isoformat() if off is not None else None
        if expected is not None:
            if pred == expected:
                tp += 1
            elif pred is None:
                fn += 1
                wrong.append((ex["text"], "missed", expected, pred))
            else:
                fp += 1
                fn += 1
                wrong.append((ex["text"], "wrong-date", expected, pred))
        else:
            if pred is None:
                tn += 1
            else:
                fp += 1
                wrong.append((ex["text"], "false-positive", expected, pred))

    precision = tp / (tp + fp) if (tp + fp) else 1.0
    recall = tp / (tp + fn) if (tp + fn) else 1.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0

    print("\n" + "=" * 60)
    print("  DEADLINE EXTRACTION EVALUATION")
    print("=" * 60)
    print(f"examples={len(data['examples'])}  TP={tp} FP={fp} FN={fn} TN={tn}")
    print(f"precision={precision:.3f}  recall={recall:.3f}  F1={f1:.3f}")
    if wrong:
        print("- misclassified:")
        for text, why, exp, got in wrong:
            print(f"    [{why}] {text!r}  expected={exp} got={got}")
    print("=" * 60 + "\n")
    return {"precision": precision, "recall": recall, "f1": f1,
            "tp": tp, "fp": fp, "fn": fn, "tn": tn}


if __name__ == "__main__":
    run()
