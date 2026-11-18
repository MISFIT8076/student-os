# Evaluating the prioritizer

This is the piece that turns Student OS from "a working build" into a project
with a **measurable result** you can defend in a viva and write up in a paper.

## Research question

> Does context-aware prioritization rank a student's cross-platform action
> items closer to human judgment than simple heuristics (due-date sorting,
> arrival order, random)?

## Method

We evaluate ranking quality offline against a labeled dataset — the standard
information-retrieval setup, so the methodology is familiar to reviewers.

**Dataset** (`eval/dataset.json`, authored in `eval/build_dataset.py`).
**40 realistic student scenarios** (exam weeks, placement season, deadline
clusters, hackathons, quiet days, buried internship mail, semester start,
registration day, and edge cases like "only noise" or "everything due today").
Each scenario is a set of action items, and each item has a hand-set human
**relevance grade**:

| grade | meaning |
| --- | --- |
| 3 | must do today |
| 2 | important soon |
| 1 | optional |
| 0 | noise (e.g. an OTP, a promo, an old notification) |

Due dates are stored as offsets from the run date (`due_offset_days`) so the
dataset never goes stale. When the harness loads a scenario it presents the
items in a **randomized-but-reproducible order** (seeded by scenario id) so no
ranker can exploit the order in which the dataset happens to be written.

The set is deliberately **balanced, not rigged**: several scenarios are pure
dated-deadline clusters where "sort by due date" is already near-optimal, so the
benchmark does not secretly favour our ranker. Grades are explicit integer
literals in `build_dataset.py`, assigned by human judgment — never computed from
the prioritizer's rules — so the evaluation is not circular.

**Rankers** (`eval/rankers.py`).

* `random` — shuffle (floor; averaged over 25 seeds for stability).
* `source_order` — arbitrary arrival order (what you'd get with no ranking).
* `due_date` — earliest due date first; undated items last. A strong, naive
  heuristic — the one worth beating.
* `prioritizer` — our context-aware ranker (`app/orchestrator/prioritizer.py`).

**Metrics** (`eval/metrics.py`, all unit-tested in `tests/test_metrics.py`).

* **nDCG@k** — normalized discounted cumulative gain at k=3 and k=5; rewards
  putting high-relevance items near the top. The primary metric.
* **P@3** — precision@3: fraction of the top 3 that are genuinely important
  (grade ≥ 2).
* **pairwise** — fraction of gold-ordered item pairs the ranking gets right
  (ties excluded); equivalent to (Kendall's τ + 1)/2 over untied pairs.
* **MRR** — mean reciprocal rank of the first "must do today" (grade 3) item.

**Statistical significance** (`eval/stats.py`, tested in `tests/test_stats.py`).
A single mean isn't enough — we test whether the improvement is real. Because
each scenario gives one nDCG@5 value per ranker, we use a **paired** design and
report, for prioritizer vs each baseline:

* **Wilcoxon signed-rank test** — a non-parametric paired test (doesn't assume
  the differences are normally distributed) on the per-scenario nDCG@5
  differences, with tie and continuity corrections. Gives the p-value. Our
  implementation is cross-checked against `scipy.stats.wilcoxon`.
* **Bootstrap 95% confidence interval** for the mean difference — an intuitive
  effect size: "the improvement is +0.07 nDCG@5, 95% CI [0.035, 0.098]".
* **Rank-biserial effect size** and **win/tie/loss** counts across scenarios.

## How to run

```bash
cd backend
python -m eval.build_dataset     # (re)generate dataset.json from the authored scenarios
python -m eval.run_eval          # prints the table + significance; writes results.json/.csv
python -m pytest tests/test_metrics.py tests/test_stats.py   # verify metrics + stats
```

## Result (40 scenarios)

Mean of each metric across the 40 scenarios (higher is better):

```
ranker              nDCG@3      nDCG@5         P@3    pairwise         MRR
--------------------------------------------------------------------------
random               0.599       0.739       0.464       0.496       0.345
source_order         0.622       0.752       0.450       0.536       0.361
due_date             0.842       0.887       0.608       0.780       0.551
prioritizer          0.930       0.954       0.725       0.905       0.662
```

**Statistical significance** (paired, on nDCG@5):

| comparison | mean Δ | 95% CI (bootstrap) | Wilcoxon p | effect r | win/tie/loss |
| --- | --- | --- | --- | --- | --- |
| prioritizer vs **due_date** | **+0.067** | [+0.035, +0.098] | **0.0004** | +0.74 | 23 / 10 / 7 |
| prioritizer vs source_order | +0.202 | [+0.140, +0.269] | 1.7e-06 | +0.92 | 34 / 4 / 2 |

**Interpretation.** The prioritizer leads on every metric, and the improvement
over the strongest baseline (due-date sorting) is **statistically significant**
(Wilcoxon p ≈ 0.0004) with a **large effect size**. The gap comes from cases due-date sorting handles badly:
undated-but-urgent items (a "recruiter is interested" email with no deadline),
noise with no date (OTPs) sinking correctly, and exam-week context pushing a
contest that's *due today* below coursework due later.

**We also lose 7 of 40** — honestly. Those are mostly pure dated-deadline
clusters where due-date sorting is already optimal. Reporting these is a feature: it shows the
benchmark is fair and points at the next improvement.

## Threats to validity (state these in the paper)

* **Single annotator, synthetic scenarios.** The 40 scenarios and their grades
  reflect one author's judgment over constructed cases. This is the biggest
  remaining threat. Strengthen it with ≥2 independent annotators grading the
  same items, and report inter-annotator agreement (Cohen's κ).
* **N = 40.** Enough for a significant paired result with a large effect size,
  but modest.
* **Offline proxy.** nDCG against labels is a proxy for real usefulness. The
  natural follow-up is a **user study**.

## Extending

* Add a **learned ranker** — train a model on the labeled data and compare it
  to the rule-based ranker.
* Add an **LLM ranker** to `rankers.py` (behind `ANTHROPIC_API_KEY`) and compare
  it to the rule-based ranker — a clean "does the LLM help ranking?" experiment.
* Grow `dataset.json`; the harness picks up new scenarios automatically.
