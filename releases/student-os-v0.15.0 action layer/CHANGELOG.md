# Changelog

All notable changes to Student OS, version by version. The project was built
incrementally — each version adds one meaningful capability on top of the last.
Format loosely follows [Keep a Changelog](https://keepachangelog.com/); versions
use [Semantic Versioning](https://semver.org/) (0.x = pre-release milestones).

---

## v0.15.0 — Action layer with guardrails *(current)*
**Theme: the app can act, safely.**
- Added `app/actions.py`: a **propose → confirm** flow for draft_reply, add_event,
  snooze, and mark_done. Nothing executes without a one-time confirmation token,
  so the agent never acts silently on the student's behalf.
- Executions are logged to the store (mark_done/snooze feed the ranker).
- New `POST /actions/propose` and `POST /actions/confirm`. Tests cover the
  single-use token, rejection of unknown tokens, and invalid actions.

## v0.14.0 — Opportunity radar + application tracking
**Theme: never miss the things that matter most in placement season.**
- Added `app/intelligence/opportunities.py`: classifies items into internships /
  scholarships / hackathons / contests and merges saved **application status**
  (new → interested → applied → offer/rejected), persisted in the store.
- New `GET /opportunities` and `POST /opportunities/status`. Tests cover
  classification, status round-trip, and validation.

## v0.13.0 — Proactive notifier
**Theme: push the brief, don't wait to be asked.**
- Added `app/notifier.py`: formats the daily brief + pre-deadline alerts and
  sends via **Telegram or email** when configured, else a safe **dry-run**.
- CLI `python -m app.notifier` for a scheduled daily run; `GET /notify/preview`
  and `POST /notify/send` endpoints. Tests cover formatting and channel logic.

## v0.12.0 — Intelligent day-scheduler + wellbeing pacing
**Theme: from a ranked list to an actual plan.**
- Added a **day-scheduler** (`app/intelligence/scheduler.py`) that time-blocks
  ranked tasks into the day's free slots, respecting effort estimates.
- **Wellbeing-aware pacing**: when there's more work than hours, it schedules the
  top-priority tasks and honestly defers the rest with gentle advice, instead of
  planning an impossible day.
- New `GET /schedule` endpoint. Tests: no overlaps, only real tasks blocked,
  overflow + overcommit detection.

## v0.11.0 — NLP deadline extraction
**Theme: catch deadlines hidden in text.**
- Added `mcp_servers/common/extraction.py` — dependency-free parsing of relative
  ("apply by Friday", "in 3 days") and absolute ("3 August", "05/08") dates.
- Wired into the **Gmail** and **Classroom** servers: emails/announcements with no
  explicit date now get a due date (marked `due_source=extracted`).
- Added a labeled extraction benchmark (`eval/extraction_eval.py`) —
  precision/recall/F1 = **1.00** on the current set — and unit tests.

## v0.10.0 — Learned ranker + persistence + feedback loop
**Theme: the project's research core.**
- Added a **persistence layer** (`app/store.py`) using SQLAlchemy — SQLite by
  default (zero setup), PostgreSQL via `DATABASE_URL`. Logs every briefing's
  items and every user action.
- Added **feedback + stats API** (`POST /feedback`, `GET /stats`) — the loop the
  ranker learns from, and the data behind a future progress dashboard.
- Added a **learning-to-rank model** (`app/intelligence/`): feature builder,
  ridge-regression trainer, and a runtime ranker that predicts item relevance.
- Made the runtime ranker **pluggable** (`RANKER=rule|learned`) with automatic
  fallback to the rule-based baseline (cold start).
- Extended the evaluation with the learned ranker under **leave-one-scenario-out
  cross-validation**: nDCG@5 **0.968** (unseen scenarios) vs 0.954 rule-based vs
  0.887 due-date; significant over both (p≈2e-5 vs due-date, p≈0.03 vs rules).
- Tests: 22 → **31 passing** (features, store, learned ranker).

## v0.9.0 — Documentation set
- Authored `docs/`: `ARCHITECTURE.md`, `SETUP.md`, `ROADMAP.md`,
  `EVALUATION.md`, the illustrated `GUIDE.html`, and the `PRODUCT_PLAN.md`
  master plan.

## v0.8.0 — Bigger benchmark + statistical significance
- Grew the eval dataset from 8 to **40 labeled scenarios** (`build_dataset.py`).
- Added a **paired significance test** (`eval/stats.py`): Wilcoxon signed-rank +
  bootstrap CI + effect size, cross-checked against scipy.

## v0.7.0 — Evaluation harness
- Added `eval/`: ranking metrics (nDCG@k, precision@k, pairwise, MRR), baseline
  rankers (random / arrival-order / due-date), and a runner producing a
  comparison table. Turned "we built it" into "we measured it."

## v0.6.0 — Google Classroom connector
- Added the Classroom MCP server (pending assignments + announcements),
  reusing the shared Google OAuth token.

## v0.5.0 — Caching layer
- Added `app/cache.py`: Redis when available, in-memory TTL cache otherwise.
- Cold briefing ~6s → **near-instant** on cache hit; `?refresh=true` to bypass.

## v0.4.0 — Real Google data (OAuth)
- Added shared Google OAuth (`mcp_servers/common/google_auth.py`) with a login
  CLI and token refresh; wired **Gmail** and **Calendar** to their real APIs.

## v0.3.0 — Codeforces connector
- Added the Codeforces MCP server (upcoming contests via the public API +
  practice reminder). Proved a new platform drops in without touching the core.

## v0.2.0 — Web app
- Added the **Next.js + TypeScript** frontend: a daily-briefing dashboard and a
  chat panel talking to the backend API.

## v0.1.0 — Initial platform
- MCP **orchestrator** (tool router) that launches servers over stdio, merges,
  and de-duplicates results.
- Three MCP servers: **GitHub** (real API + mock), **Gmail**, **Calendar** (mock
  + OAuth-ready).
- **Context-aware prioritizer** (rule-based, exam-week logic) + unit tests.
- **FastAPI** backend (`/briefing`, `/chat`, `/tools`, `/health`).
- **Mock mode** so the whole system runs end-to-end with zero credentials.

---

### Legend of where each version lives in the code
`app/orchestrator/` (routing + ranking) · `mcp_servers/` (connectors) ·
`app/cache.py` (caching) · `app/store.py` (persistence) · `app/intelligence/`
(learning) · `eval/` (evaluation) · `frontend/` (web app) · `docs/` (writing).
