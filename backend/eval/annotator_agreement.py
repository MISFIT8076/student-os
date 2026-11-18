"""Compute inter-annotator agreement for the second-annotator grading sheet.

    cd backend && python -m eval.annotator_agreement [path/to/filled_annotator_sheet.xlsx]

Compares a second rater's grades (from study_kit/annotator_sheet.xlsx) against
the dataset's original gold grades and reports:
  * exact agreement %
  * Cohen's kappa (unweighted)
  * quadratic-weighted kappa (appropriate for the ordinal 0-3 scale)

A high kappa is the evidence that the gold labels are reliable, not one person's
idiosyncratic opinion — directly answering the "single-annotator" limitation in
docs/EVALUATION.md.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
DATASET = REPO / "backend" / "eval" / "dataset.json"
DEFAULT_SHEET = REPO / "study_kit" / "annotator_sheet.xlsx"
K = 4  # categories 0..3


def _gold_by_number() -> dict[int, int]:
    import json

    data = json.loads(DATASET.read_text())
    gold, n = {}, 0
    for sc in data["scenarios"]:
        for it in sc["items"]:
            n += 1
            gold[n] = int(it["relevance"])
    return gold


def _read_annotator(path: Path) -> dict[int, int]:
    from openpyxl import load_workbook

    wb = load_workbook(path, data_only=True)
    gs = wb["Grading"]
    header = [c.value for c in gs[1]]
    no_col = header.index("No.") + 1
    grade_col = header.index("Your grade (0-3)") + 1
    out: dict[int, int] = {}
    for row in gs.iter_rows(min_row=2):
        no = row[no_col - 1].value
        g = row[grade_col - 1].value
        if no is None or g is None or g == "":
            continue
        try:
            out[int(no)] = int(g)
        except (ValueError, TypeError):
            continue
    return out


def _kappa(pairs: list[tuple[int, int]], weighted: bool) -> float:
    n = len(pairs)
    if n == 0:
        return 0.0
    obs = [[0.0] * K for _ in range(K)]
    r = [0.0] * K
    c = [0.0] * K
    for a, b in pairs:
        obs[a][b] += 1
        r[a] += 1
        c[b] += 1

    def w(i, j):
        if not weighted:
            return 1.0 if i == j else 0.0
        return 1.0 - ((i - j) ** 2) / ((K - 1) ** 2)  # quadratic

    po = sum(w(i, j) * obs[i][j] for i in range(K) for j in range(K)) / n
    pe = sum(w(i, j) * (r[i] / n) * (c[j] / n) for i in range(K) for j in range(K))
    return (po - pe) / (1 - pe) if (1 - pe) else 1.0


def _band(k: float) -> str:
    if k < 0.0:
        return "poor"
    if k < 0.20:
        return "slight"
    if k < 0.40:
        return "fair"
    if k < 0.60:
        return "moderate"
    if k < 0.80:
        return "substantial"
    return "almost perfect"


def run(path: Path) -> dict:
    gold = _gold_by_number()
    annot = _read_annotator(path)
    pairs = [(gold[no], annot[no]) for no in annot if no in gold]

    print("\n" + "=" * 60)
    print("  INTER-ANNOTATOR AGREEMENT")
    print("=" * 60)
    if not pairs:
        print("No grades found yet — fill the yellow 'Your grade' column and re-run.")
        print("=" * 60 + "\n")
        return {"graded": 0}

    exact = sum(1 for a, b in pairs if a == b) / len(pairs)
    k = _kappa(pairs, weighted=False)
    kw = _kappa(pairs, weighted=True)
    print(f"items graded          : {len(pairs)} / {len(gold)}")
    print(f"exact agreement       : {exact:.1%}")
    print(f"Cohen's kappa         : {k:.3f}  ({_band(k)})")
    print(f"weighted kappa (quad) : {kw:.3f}  ({_band(kw)})")
    print("=" * 60 + "\n")
    return {"graded": len(pairs), "exact": exact, "kappa": k, "weighted_kappa": kw}


if __name__ == "__main__":
    sheet = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_SHEET
    if not sheet.exists():
        print(f"Sheet not found: {sheet}\nBuild it: python study_kit/build_annotator_sheet.py")
        sys.exit(1)
    run(sheet)
