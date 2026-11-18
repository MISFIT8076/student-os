"""Train the learned ranker on the labeled scenarios.

    cd backend && python -m app.intelligence.train

Learns a linear model that predicts an item's relevance (0-3) from its
features; at serve time we rank by predicted relevance. Trained with ridge
regression (closed-form, no heavy ML dependency) on eval/dataset.json.

Saves weights to app/intelligence/ranker_weights.json and prints a quick
leave-one-scenario-out (LOSO) nDCG@5 sanity check. The *rigorous* comparison
against the rule-based baseline lives in eval/run_eval.py.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from app.intelligence.features import FEATURE_NAMES, featurize, vectorize
from eval.metrics import ndcg_at_k

DATASET = Path(__file__).resolve().parents[2] / "eval" / "dataset.json"
WEIGHTS = Path(__file__).resolve().parent / "ranker_weights.json"
LAMBDA = 1.0  # ridge regularization strength


def _exam_week(items: list[dict]) -> bool:
    for it in items:
        if it["kind"] == "exam":
            off = it.get("due_offset_days")
            if off is not None and 0 <= off <= 5:
                return True
    return False


def _scenario_matrix(scenario: dict):
    """Return (X rows, y labels) for one scenario."""
    exam = _exam_week(scenario["items"])
    X, y = [], []
    for it in scenario["items"]:
        feats = featurize(
            source=it["source"],
            kind=it["kind"],
            days_until=it.get("due_offset_days"),
            category=it.get("category"),
            title=it["title"],
            detail=it.get("detail", ""),
            exam_week=exam,
        )
        X.append(vectorize(feats))
        y.append(float(it["relevance"]))
    return np.array(X, dtype=float), np.array(y, dtype=float)


def train_ridge(X: np.ndarray, y: np.ndarray, lam: float = LAMBDA):
    """Closed-form ridge regression with an unregularized bias term."""
    n, d = X.shape
    Xb = np.hstack([X, np.ones((n, 1))])          # add bias column
    reg = lam * np.eye(d + 1)
    reg[-1, -1] = 0.0                              # don't regularize the bias
    w_full = np.linalg.solve(Xb.T @ Xb + reg, Xb.T @ y)
    return w_full[:-1], float(w_full[-1])


def _ndcg_for(scenario: dict, w: np.ndarray, b: float) -> float:
    X, y = _scenario_matrix(scenario)
    scores = X @ w + b
    order = np.argsort(-scores)                    # descending predicted score
    ranked_gold = [float(y[i]) for i in order]
    return ndcg_at_k(ranked_gold, 5)


def main() -> None:
    data = json.loads(DATASET.read_text())
    scenarios = data["scenarios"]

    # Full-data model (this is what we deploy).
    Xs = [_scenario_matrix(s) for s in scenarios]
    X_all = np.vstack([x for x, _ in Xs])
    y_all = np.concatenate([y for _, y in Xs])
    w, b = train_ridge(X_all, y_all)

    WEIGHTS.write_text(json.dumps({
        "feature_names": FEATURE_NAMES,
        "weights": w.tolist(),
        "bias": b,
        "lambda": LAMBDA,
        "trained_on": DATASET.name,
        "n_items": int(X_all.shape[0]),
        "n_scenarios": len(scenarios),
    }, indent=2))

    # Quick honesty check: leave-one-scenario-out CV nDCG@5.
    loso = []
    for i, s in enumerate(scenarios):
        rest = [Xs[j] for j in range(len(scenarios)) if j != i]
        Xtr = np.vstack([x for x, _ in rest])
        ytr = np.concatenate([y for _, y in rest])
        wi, bi = train_ridge(Xtr, ytr)
        loso.append(_ndcg_for(s, wi, bi))

    print(f"Trained on {X_all.shape[0]} items / {len(scenarios)} scenarios, "
          f"{len(FEATURE_NAMES)} features.")
    print(f"Saved weights -> {WEIGHTS}")
    print(f"LOSO-CV nDCG@5 (unseen scenarios): {np.mean(loso):.3f}")
    print("Top positive signals:")
    for name, weight in sorted(zip(FEATURE_NAMES, w), key=lambda t: -t[1])[:6]:
        print(f"  {name:<22} {weight:+.2f}")


if __name__ == "__main__":
    main()
