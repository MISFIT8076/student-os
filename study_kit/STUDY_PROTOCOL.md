# Student OS — Study Protocol

This kit turns the remaining (non-code) plan item — the **user study** — into a
run-it-yourself package. It has two independent parts; do both for the strongest
report.

## What's in this folder

| File | Purpose |
| --- | --- |
| `CONSENT_FORM.docx` | Print & have each participant sign before taking part |
| `SURVEYS.docx` | Pre-study + post-study questionnaires (print, or copy into Google Forms) |
| `annotator_sheet.xlsx` | Blind grading sheet for a second annotator (all 40 scenarios) |
| `build_annotator_sheet.py` | Regenerates the sheet from the dataset |
| `STUDY_PROTOCOL.md` | This file |

The scorer lives with the code: `backend/eval/annotator_agreement.py`.

---

## Part 1 — Validate the labels (½ day, 1 helper)

**Goal:** show the 40-scenario benchmark isn't one person's opinion. Answers the
"single-annotator" limitation in `docs/EVALUATION.md`.

1. Give `annotator_sheet.xlsx` to **one classmate** who did *not* build the
   dataset. They read the scale on the Instructions tab and fill the yellow
   **"Your grade (0–3)"** column for all 221 items — independently, without
   seeing the original grades.
2. Score agreement:
   ```bash
   cd backend
   python -m eval.annotator_agreement ../study_kit/annotator_sheet.xlsx
   ```
   It prints exact agreement, **Cohen's kappa**, and **quadratic-weighted kappa**.
3. Report the kappa in the paper. **κ ≥ 0.6 (substantial)** means the labels are
   reliable; weighted kappa is the fairer number for an ordinal 0–3 scale.

---

## Part 2 — Two-week user study (2 weeks, ~10–15 participants)

**Research question:** does using Student OS reduce missed deadlines and
overwhelm, and is it usable?

**Design (within-subjects, simplest to run):**

1. **Recruit** ~10–15 students; have each sign `CONSENT_FORM.docx`. Assign each an
   anonymous ID (P01, P02, …).
2. **Baseline (pre-survey):** before they start, each fills the **Pre-Study
   Survey** — apps checked/day, deadlines missed in the last 2 weeks, overwhelm
   and "on top of things" (1–5), time spent/day.
3. **Use it for 2 weeks:** participants use Student OS as part of their routine
   (real accounts via `docs/SETUP.md`, or the sample "mock" mode if they prefer
   not to connect accounts). Encourage a daily glance at the briefing.
4. **Post-survey:** each fills the **Post-Study Survey** — the same four metrics
   again (for a before/after comparison), the 10-item **SUS** usability scale,
   and impact questions.
5. **Analyse:**
   - *Missed deadlines* and *overwhelm*: compare each participant's pre vs post
     numbers. Use a **paired Wilcoxon signed-rank test** (you already have the
     implementation in `eval/stats.py`) — report the median change and p-value.
   - *Usability*: compute the **SUS score** per participant (see below), report
     the mean (68 is "average"; 80+ is excellent).
   - *Adoption*: % who answered "Yes/Maybe" to "would you keep using it".

**SUS scoring:** items alternate positive (1,3,5,7,9) and negative (2,4,6,8,10).
For odd items score = (answer − 1); for even items score = (5 − answer). Sum the
10 scores and multiply by 2.5 → a 0–100 SUS score.

---

## Ethics checklist

- Signed consent from every participant before any data is collected.
- Anonymous IDs only; no names in the analysis or report.
- Account access is read-only; participants may use mock mode; they can withdraw
  at any time and have their data deleted.
- If your department has an ethics/records committee, get its sign-off first.

## What to write in the thesis

> *"On 40 scenarios, a second annotator agreed with our labels at κ = X
> (weighted κ = Y), confirming label reliability. In a two-week study with N
> students, self-reported missed deadlines fell from A to B (Wilcoxon p = …) and
> overwhelm from C to D; mean SUS usability was S/100, and Z% would continue
> using the system."*

Fill in X, Y, A, B, … from your results and you have a complete, evidence-backed
evaluation section.
