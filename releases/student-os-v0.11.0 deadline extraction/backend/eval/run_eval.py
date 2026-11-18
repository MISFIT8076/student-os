"""Run the prioritizer evaluation and print a baseline-vs-ours comparison.

    cd backend && python -m eval.run_eval

Loads the labeled scenarios, runs each ranker, computes ranking metrics per
scenario, aggregates mean±std across scenarios, prints a table, and writes
eval/results.json and eval/results.csv for the report.
"""
from __future__ import annotations

import csv
import json
import random
import statistics
import zlib
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from app.schemas import ActionItem
from eval.metrics import mrr, ndcg_at_k, pairwise_accuracy, precision_at_k
from eval.rankers import BASELINES, prioritizer_ranker
from eval.stats import bootstrap_ci_mean, wilcoxon_signed_rank, win_tie_loss

# The metric the significance tests run on, and the paired comparisons we make.
SIG_METRIC = "nDCG@5"
SIG_PAIRS = [
    ("prioritizer", "due_date"),
    ("learned", "due_date"),
    ("learned", "prioritizer"),
]

HERE = Path(__file__).resolve().parent
DATASET = HERE / "dataset.json"
RANDOM_SEEDS = 25  # average the random baseline over many shuffles

# Column order for the metric table.
METRICS = ["nDCG@3", "nDCG@5", "P@3", "pairwise", "MRR"]
# Ranker display order — the two systems (rule-based, learned) last.
RANKER_ORDER = ["random", "source_order", "due_date", "prioritizer", "learned"]


def _build_items(scenario: dict, ref: date) -> list[ActionItem]:
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
    # Present items in a randomized-but-reproducible "arrival order" so that no
    # ranker (especially source_order) can exploit how the dataset was authored.
    seed = zlib.crc32(scenario["id"].encode())
    random.Random(seed).shuffle(items)
    return items


def _gold_sequence(ranked: list[ActionItem]) -> list[float]:
    return [float(it.raw["_gold"]) for it in ranked]


def _metrics_for(rels: list[float]) -> dict[str, float]:
    return {
        "nDCG@3": ndcg_at_k(rels, 3),
        "nDCG@5": ndcg_at_k(rels, 5),
        "P@3": precision_at_k(rels, 3, threshold=2.0),
        "pairwise": pairwise_accuracy(rels),
        "MRR": mrr(rels, threshold=3.0),
    }


def _score_ranker(name: str, items: list[ActionItem], ref: date) -> dict[str, float]:
    """Return one metric dict for a ranker on one scenario."""
    if name == "prioritizer":
        return _metrics_for(_gold_sequence(prioritizer_ranker(items, ref=ref)))
    if name == "random":
        # Average metrics over many seeds for a stable floor.
        acc: dict[str, list[float]] = {m: [] for m in METRICS}
        for seed in range(RANDOM_SEEDS):
            rels = _gold_sequence(BASELINES["random"](items, seed=seed))
            for m, v in _metrics_for(rels).items():
                acc[m].append(v)
        return {m: statistics.mean(vs) for m, vs in acc.items()}
    return _metrics_for(_gold_sequence(BASELINES[name](items)))


def _learned_loso(scenarios: list[dict]) -> dict[str, list[float]]:
    """Leave-one-scenario-out predictions for the learned ranker.

    For each scenario we train the ridge model on ALL OTHER scenarios and
    predict this one — so the learned ranker is always evaluated on unseen
    data (no training on the test set). Returns sid -> gold relevances in the
    model's predicted order.
    """
    import numpy as np

    from app.intelligence.train import _scenario_matrix, train_ridge

    mats = [_scenario_matrix(s) for s in scenarios]  # [(X, y), ...]
    out: dict[str, list[float]] = {}
    for i, sc in enumerate(scenarios):
        others = [mats[j] for j in range(len(scenarios)) if j != i]
        x_tr = np.vstack([x for x, _ in others])
        y_tr = np.concatenate([y for _, y in others])
        w, b = train_ridge(x_tr, y_tr)
        x_i, y_i = mats[i]
        scores = x_i @ w + b
        order = np.argsort(-scores)
        out[sc["id"]] = [float(y_i[k]) for k in order]
    return out


def run() -> dict:
    data = json.loads(DATASET.read_text())
    scenarios = data["scenarios"]
    ref = date.today()

    # per_ranker[name][metric] = list of per-scenario values
    per_ranker: dict[str, dict[str, list[float]]] = {
        r: {m: [] for m in METRICS} for r in RANKER_ORDER
    }
    per_scenario: dict[str, dict[str, dict[str, float]]] = {}

    learned_scores = _learned_loso(scenarios)  # honest LOSO cross-validation

    for sc in scenarios:
        items = _build_items(sc, ref)
        per_scenario[sc["id"]] = {}
        for name in RANKER_ORDER:
            if name == "learned":
                metrics = _metrics_for(learned_scores[sc["id"]])
            else:
                metrics = _score_ranker(name, items, ref)
            per_scenario[sc["id"]][name] = metrics
            for m, v in metrics.items():
                per_ranker[name][m].append(v)

    summary = {
        name: {
            m: {
                "mean": statistics.mean(vals),
                "std": statistics.pstdev(vals) if len(vals) > 1 else 0.0,
            }
            for m, vals in metrics.items()
        }
        for name, metrics in per_ranker.items()
    }

    # Paired significance for each configured comparison on the chosen metric.
    sids = [sc["id"] for sc in scenarios]
    significance = {}
    for a, b in SIG_PAIRS:
        a_vals = [per_scenario[s][a][SIG_METRIC] for s in sids]
        b_vals = [per_scenario[s][b][SIG_METRIC] for s in sids]
        diffs = [x - y for x, y in zip(a_vals, b_vals)]
        significance[f"{a}_vs_{b}"] = {
            "metric": SIG_METRIC,
            "wilcoxon": wilcoxon_signed_rank(diffs),
            "mean_diff_ci95": bootstrap_ci_mean(diffs),
            "win_tie_loss": win_tie_loss(a_vals, b_vals),
        }

    result = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "n_scenarios": len(scenarios),
        "random_seeds": RANDOM_SEEDS,
        "significance_metric": SIG_METRIC,
        "summary": summary,
        "significance": significance,
        "per_scenario": per_scenario,
    }
    _write_outputs(result)
    _print_table(summary, result)
    return result


def _write_outputs(result: dict) -> None:
    (HERE / "results.json").write_text(json.dumps(result, indent=2))
    with (HERE / "results.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["ranker", "metric", "mean", "std"])
        for name, metrics in result["summary"].items():
            for m, stat in metrics.items():
                w.writerow([name, m, f"{stat['mean']:.4f}", f"{stat['std']:.4f}"])


def _print_table(summary: dict, result: dict) -> None:
    print("\n" + "=" * 74)
    print(f"  PRIORITIZER EVALUATION  ·  {result['n_scenarios']} scenarios  ·  "
          f"random avg over {result['random_seeds']} seeds")
    print("=" * 74)
    header = f"{'ranker':<14}" + "".join(f"{m:>12}" for m in METRICS)
    print(header)
    print("-" * 74)
    for name in RANKER_ORDER:
        row = f"{name:<14}"
        for m in METRICS:
            row += f"{summary[name][m]['mean']:>12.3f}"
        print(row)
    print("-" * 74)
    print("(higher is better for every metric; values are means across scenarios)")
    print("\n" + "-" * 74)
    print(f"SIGNIFICANCE  ·  paired Wilcoxon on {result['significance_metric']}  ·  "
          f"{result['n_scenarios']} scenarios")
    print("-" * 74)
    for pair, s in result["significance"].items():
        w, ci, wtl = s["wilcoxon"], s["mean_diff_ci95"], s["win_tie_loss"]
        label = pair.replace("_vs_", " vs ")
        sig = "significant" if w["p_value"] < 0.05 else "not significant"
        print(f"{label:<26} meanΔ={ci['mean']:+.3f}  95% CI [{ci['low']:+.3f},{ci['high']:+.3f}]"
              f"  p={w['p_value']:.4g} ({sig})")
        print(f"{'':<27}n={w['n']}  effect r={w['rank_biserial']:+.2f}  "
              f"win/tie/loss = {wtl['win']}/{wtl['tie']}/{wtl['loss']}")
    print("-" * 74)
    print("Full results written to eval/results.json and eval/results.csv\n")


if __name__ == "__main__":
    run()
