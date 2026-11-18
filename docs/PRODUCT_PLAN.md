# Student OS — Product & Technical Master Plan

*How we turn a working integration into a genuinely useful, research-grade
final-year IT project — designed from the student's point of view.*

This plan takes the platform we already have (5 MCP connectors, an orchestrator,
a rule-based prioritizer, a caching layer, an evaluation harness) and layers on
the things a real student actually needs. Every feature below is justified by a
student need, not by "it's cool tech."

> **Status (v0.18):** all Must/Should/Could **code** features below are now
> implemented and tested — learning-to-rank, NLP deadline extraction,
> persistence + feedback, security hardening, day-scheduler + pacing, proactive
> notifier, opportunity radar, action layer, progress dashboard, and the RAG
> study assistant. The only remaining item is the **user study** (non-code —
> needs real student participants). See `CHANGELOG.md` for the version map.

---

## 1. Who we're building for (put yourself in their shoes)

**Persona — "Aarav", 4th-year IT student.** Placement season. He's chasing
internships, keeping up with coursework, doing DSA practice, and running his
FYP. His pain isn't a lack of apps — it's the *mental tax* of stitching 8 apps
together every morning and the fear of missing the one email that mattered.

**A day in his life, and where we help:**

| Moment | What Aarav thinks | What Student OS should do |
| --- | --- | --- |
| 8:00 wakes up | "What actually needs me today?" | A single prioritized brief, personalized to him |
| 8:05 | "Did I miss any deadline hidden in email?" | Extract deadlines from mail/announcements, not just Calendar |
| 8:10 | "When will I even do all this?" | Fit tasks into his free slots around classes |
| 12:00 recruiter mail | "Reply before I forget" | Draft a reply he just approves; add follow-up to plan |
| 18:00 | "Am I keeping up? practice streak?" | Progress + habit tracking |
| Any time | "Is my data safe?" | Read-only scopes, no leaks, resistant to malicious content |
| Evening | "Don't make me open the app" | Push the brief + pre-deadline nudges to Telegram/email |

**Jobs-to-be-done (the north star):** (1) *Tell me what matters now*, (2) *don't
let me miss anything*, (3) *help me fit it into my day*, (4) *surface
opportunities*, (5) *let me act quickly*, (6) *show me I'm on track*, (7) *keep
me safe and calm*.

---

## 2. Feature modules (the four spines + what students need)

Prioritized with **MoSCoW** (Must / Should / Could) so scope stays realistic for
a 3-person team. The four research spines are marked ⭐.

### MUST-HAVE — the core contribution + essentials

- **⭐ Personalized learning-to-rank prioritizer.** Replace fixed weights with a
  model that learns each student's priorities from their own actions (opened,
  done, dismissed, snoozed). Falls back to the rule-based ranker for new users
  (cold start). *Need #1, #7.* Reuses `eval/` for measurement.
- **⭐ NLP deadline & task extraction.** Detect deadlines/tasks buried in email
  and Classroom text ("apply by Friday", "submit before 5 pm") and turn them
  into dated action items. *Need #2.* Fixes today's gap where only Calendar has
  dates.
- **Persistence + feedback loop (PostgreSQL).** Store item history, user actions,
  and learned preferences. This is what makes learning, progress tracking, and
  analytics possible — and finally uses the database in the proposal.
- **⭐ Security & privacy layer.** Least-privilege read-only scopes, an encrypted
  token vault, and a **prompt-injection sanitizer** that cleans email/tool text
  before it reaches the LLM. *Need #7.*
- **Offline evaluation + a small user study.** Extend the existing benchmark;
  run a 2-week study with ~15 students. *This is what makes claims credible.*

### SHOULD-HAVE — high student value, achievable

- **⭐ Intelligent day-scheduler.** Turn the ranked list into a time-blocked plan
  that fits tasks into free calendar slots, respecting deadlines and estimated
  durations (optimization / constraint solving). *Need #3.*
- **Proactive daily brief + reminders.** A scheduled agent that pushes the brief
  and pre-deadline nudges to **Telegram/email**, and flags changes ("deadline
  moved", "new internship"). *Need #2, and "don't make me open the app."*
- **Opportunity radar.** Aggregate internships / scholarships / hackathons /
  contests, track application deadlines and status (applied / pending / closed).
  *Need #4 — the placement-season killer feature.*
- **Action layer with guardrails.** Safe write-actions — draft an email reply,
  add a calendar event, snooze, mark done — always behind a one-tap
  confirmation. *Need #5.*

### COULD-HAVE — stretch, if time allows

- **Progress & habit dashboard.** Coursework kept-up %, coding-practice streak,
  application funnel — charts over the stored history. *Need #6.*
- **Study-material assistant (RAG).** Index notes/PDFs/Drive and answer questions
  over them ("what did the OS lecture say about paging?").
- **Wellbeing-aware pacing.** Detect over-commitment and suggest a realistic day
  instead of an impossible one. *Keeps Aarav calm, not anxious.*

---

## 3. Target architecture (extends what we already built)

```
             ┌───────────────────────── Delivery ─────────────────────────┐
             │   Web dashboard (Next.js)        Notifier (Telegram / email) │
             └───────────────▲───────────────────────────▲─────────────────┘
                             │ REST                        │ scheduled push
                    ┌────────┴────────────────────────────┴───────┐
                    │              Backend API (FastAPI)           │
                    │  briefing · chat · actions · feedback · stats│
                    └───┬───────────────┬───────────────┬──────────┘
        ┌───────────────┘               │               └───────────────┐
        ▼                               ▼                               ▼
 Intelligence                    Orchestrator                    Action layer (NEW)
 ─ feature builder               ─ MCP tool router               ─ draft reply / add event
 ─ ⭐ learning-to-rank            ─ dedupe + cache                 ─ guardrail + confirm
 ─ ⭐ scheduler (optim.)          │                               (write via MCP tools)
        │                        ▼
        │                 MCP servers (existing 5)  ── ⭐ NLP extractor (NEW)
        │                 GitHub · Gmail · Calendar     pulls deadlines/tasks
        │                 Codeforces · Classroom        out of unstructured text
        ▼                        │
 ⭐ Security layer (NEW)          ▼
 scope minimize · token       Real APIs (Google, GitHub, Codeforces)
 vault · injection sanitizer
        │
        ▼
 PostgreSQL (NEW): items history · user actions/feedback · learned profile · schedules
```

What's **reused**: the MCP servers, orchestrator/`mcp_manager`, `ActionItem`
schema, the rule-based prioritizer (now the *baseline* and cold-start fallback),
the cache, and the whole `eval/` harness. What's **new**: PostgreSQL persistence,
the NLP extractor, the learnable ranker + feature builder, the scheduler, the
action + security layers, and the notifier.

---

## 4. The research core: data & ML plan

This is what makes it an IT research project rather than plumbing.

**Signals we log (PostgreSQL).** For every item shown: its features + what the
student did (opened / completed / dismissed / snoozed / ignored) and when,
relative to any deadline.

**Features per item.** source, kind, due-proximity, has-deadline, category
(internship/academic/otp), extracted-vs-calendar, estimated duration,
sender/source importance (learned), time-of-day fit, and the student's
historical engagement with that source/kind.

**Model.** Start interpretable and small-data-friendly: logistic regression or
gradient-boosted trees, then a **learning-to-rank** model (e.g. LambdaMART) that
optimizes nDCG directly. Personalize via per-user features (or per-user weights
over a global model); cold-start falls back to the rule-based ranker.

**Training label.** Two sources: (a) the offline **gold grades** in the
benchmark, and (b) **implicit feedback** (did the student act on it promptly?).

**Extraction model.** Rule/regex + `dateparser` as a baseline, then an
LLM-based extractor; evaluate both.

---

## 5. Evaluation plan (the evidence)

| What | How | Metric |
| --- | --- | --- |
| Ranking quality | Extend `eval/` benchmark; learned vs rule-based vs due-date | nDCG@k, Wilcoxon (already built) |
| Personalization | Per-user held-out feedback; with vs without learning | nDCG lift, top-k accuracy |
| Deadline extraction | Labeled set of ~200 emails/announcements | precision / recall / F1 |
| Scheduler | Simulated + real days | % deadlines met, slot utilization, violations |
| **User study (n≈15, 2 weeks)** | A/B: personalized vs baseline week | missed deadlines ↓, overwhelm (Likert) ↓, SUS usability |
| Security | Red-team injection test suite | % attacks blocked |

The user study is the single most valuable piece — it converts synthetic numbers
into "real students missed fewer deadlines," which is what wins a viva.

---

## 6. Who does what (3-person split)

| Member | Owns | Key deliverables |
| --- | --- | --- |
| **M1 — Platform & Data** | MCP servers, OAuth, PostgreSQL schema, feedback logging, notifier + scheduling, deployment | reliable data layer + push notifications |
| **M2 — Intelligence** | NLP extractor, feature builder, learning-to-rank model, scheduler, all experiments | the research core + results |
| **M3 — Product & Study + Security** | frontend, action/guardrail layer, security hardening + red-team, user study | usable app + evidence + trust |

Each member owns a chapter of the report and a clear experiment, so contributions
are individually assessable.

---

## 7. Phased timeline (adapt to weeks remaining)

1. **Foundation** — PostgreSQL schema + feedback logging; make the ranker a
   pluggable interface (rule-based = baseline). *Unblocks everything.*
2. **Extraction + features** — NLP deadline/task extraction; feature builder
   writing to the store.
3. **Learning-to-rank** — train the model; run the offline benchmark
   (learned vs baseline vs due-date).
4. **Scheduler + notifier + actions** — day-planning, Telegram/email push, safe
   write-actions with confirmation.
5. **Security hardening** — scopes, token vault, injection defense + red-team.
6. **User study** — recruit ~15 students, run the 2-week A/B, collect metrics.
7. **Write-up** — thesis, results, threats to validity, demo, viva prep.

If time gets tight, cut in this order: RAG assistant → wellbeing pacing →
scheduler optimization (keep a greedy version) — never cut the learning-to-rank
core, the study, or security.

---

## 8. Risks & how we manage them

- **Little real feedback data (cold start).** Seed with the rule-based prior and
  semi-synthetic feedback; the study then supplies real signal.
- **Privacy/consent for the study.** Use participants' own accounts with informed
  consent; store only what's needed; offer a mock/demo mode for grading.
- **LinkedIn / LeetCode have no open API.** Already handled: catch LinkedIn via
  Gmail; use Codeforces instead of LeetCode. State it as a design decision.
- **Scope creep.** MoSCoW above + the explicit cut-list keep a 3-person team safe.

---

## 9. One-line thesis

> **Student OS: a personalized, learning-based prioritization-and-planning agent
> over heterogeneous student data streams (via the Model Context Protocol), with
> NLP deadline extraction, safe action execution, and a security-hardened design
> — evaluated with an offline ranking benchmark and a two-week user study.**

That sentence has a platform (MCP integration), a contribution (personalized
learning-to-rank + planning + extraction), a safety story (security), and
evidence (benchmark + user study) — everything a strong IT final-year project
needs.

---

## 10. Recommended first move

Build the **Foundation** (Phase 1) now: the PostgreSQL schema + a feedback-logging
API + turning the ranker into a pluggable interface. It's the dependency for the
ML core, the progress dashboard, and the study — and it adds the database depth
examiners expect. Everything else slots on top of it.
