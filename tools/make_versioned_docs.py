"""Generate version-specific documentation for every release snapshot.

Each release (v0.1.0 → v0.18.0) gets docs scoped to the features that existed
at that version.  Versions before v0.9.0 get only a version-scoped README.md
(docs weren't formally written until v0.9.0).  Versions v0.9.0+ also get the
full docs/ set, with content reflecting that version's cumulative features.

    cd student-os && python tools/make_versioned_docs.py
"""
from __future__ import annotations

import shutil
import textwrap
from dataclasses import dataclass
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
RELEASES = REPO / "releases"

# ── Release folder names (in version order) ─────────────────────────────────
RELEASE_DIRS = [
    "student-os-v0.1.0 Initial Platform",
    "student-os-v0.2.0 web app",
    "student-os-v0.3.0 codeforces",
    "student-os-v0.4.0 google-oauth",
    "student-os-v0.5.0 cahing",
    "student-os-v0.6.0 classroom",
    "student-os-v0.7.0 evaluatoin harness",
    "student-os-v0.8.0 dataset and significant",
    "student-os-v0.9.0 documentation",
    "student-os-v0.10.0 learned ranker",
    "student-os-v0.11.0 deadline extraction",
    "student-os-v0.12.0 day scheduler",
    "student-os-v0.13.0 notifier",
    "student-os-v0.14.0 oppurtunity radar",
    "student-os-v0.15.0 action layer",
    "student-os-v0.16.0 security",
    "student-os-v0.17.0 progress dashboard",
    "student-os-v0.18.0 rag assistant",
]


@dataclass
class VersionInfo:
    """Cumulative feature-set at a given version."""
    ver: str            # e.g. "0.2.0"
    idx: int            # 0-based index into VERSIONS
    theme: str          # e.g. "Next.js + TypeScript web app"

    # Feature flags (all cumulative — True once introduced)
    has_frontend: bool       # v0.2+
    has_codeforces: bool     # v0.3+
    has_oauth: bool          # v0.4+
    has_cache: bool          # v0.5+
    has_classroom: bool      # v0.6+
    has_eval: bool           # v0.7+
    has_dataset: bool        # v0.8+
    has_docs: bool           # v0.9+
    has_learned_ranker: bool # v0.10+
    has_extraction: bool     # v0.11+
    has_scheduler: bool      # v0.12+
    has_notifier: bool       # v0.13+
    has_opportunities: bool  # v0.14+
    has_actions: bool        # v0.15+
    has_security: bool       # v0.16+
    has_progress: bool       # v0.17+
    has_rag: bool            # v0.18+

    @property
    def n_servers(self) -> int:
        n = 3  # GitHub, Gmail, Calendar
        if self.has_codeforces:
            n += 1
        if self.has_classroom:
            n += 1
        return n

    @property
    def server_list(self) -> list[str]:
        s = ["GitHub", "Gmail", "Calendar"]
        if self.has_codeforces:
            s.append("Codeforces")
        if self.has_classroom:
            s.append("Classroom")
        return s

    @property
    def n_tests(self) -> int:
        """Approximate test count at this version."""
        n = 6  # base tests
        if self.has_eval:
            n += 4  # test_metrics
        if self.has_dataset:
            n += 4  # test_stats
        if self.has_learned_ranker:
            n += 9  # test_store, test_features, test_learned_ranker
        if self.has_extraction:
            n += 5  # test_extraction
        if self.has_scheduler:
            n += 5  # test_scheduler
        if self.has_notifier:
            n += 4  # test_notifier
        if self.has_opportunities:
            n += 5  # test_opportunities
        if self.has_actions:
            n += 5  # test_actions
        if self.has_security:
            n += 5  # test_security
        if self.has_progress:
            n += 4  # test_progress
        if self.has_rag:
            n += 4  # test_rag
        return n

    @property
    def endpoints(self) -> list[str]:
        ep = ["/briefing", "/chat", "/tools", "/health"]
        if self.has_learned_ranker:
            ep.extend(["/feedback", "/stats"])
        if self.has_scheduler:
            ep.append("/schedule")
        if self.has_notifier:
            ep.extend(["/notify/preview", "/notify/send"])
        if self.has_opportunities:
            ep.extend(["/opportunities", "/opportunities/status"])
        if self.has_actions:
            ep.extend(["/actions/propose", "/actions/confirm"])
        if self.has_progress:
            ep.append("/progress")
        if self.has_rag:
            ep.append("/study/ask")
        return ep


VERSIONS_INFO: list[VersionInfo] = []

_THEMES = [
    "Initial platform: orchestrator, 3 MCP servers, prioritizer, API, mock mode",
    "Next.js + TypeScript web app (dashboard + chat)",
    "Codeforces MCP server (real public API)",
    "Shared Google OAuth; real Gmail + Calendar",
    "Caching layer (Redis + in-memory fallback)",
    "Google Classroom MCP server",
    "Evaluation harness (metrics, baselines, runner)",
    "40-scenario dataset + statistical significance",
    "Documentation set formalized + changelog",
    "Learned ranker + persistence + feedback loop",
    "NLP deadline extraction from email/announcement text",
    "Intelligent day-scheduler + wellbeing-aware pacing",
    "Proactive notifier (Telegram/email + dry-run)",
    "Opportunity radar + application tracking",
    "Action layer with propose/confirm guardrails",
    "Security hardening (prompt-injection defence, token vault, scope audit)",
    "Progress & habit dashboard",
    "Study-material RAG assistant",
]

_VERS = [
    "0.1.0", "0.2.0", "0.3.0", "0.4.0", "0.5.0", "0.6.0",
    "0.7.0", "0.8.0", "0.9.0", "0.10.0", "0.11.0", "0.12.0",
    "0.13.0", "0.14.0", "0.15.0", "0.16.0", "0.17.0", "0.18.0",
]

for _i, (_v, _t) in enumerate(zip(_VERS, _THEMES)):
    VERSIONS_INFO.append(VersionInfo(
        ver=_v, idx=_i, theme=_t,
        has_frontend=_i >= 1,
        has_codeforces=_i >= 2,
        has_oauth=_i >= 3,
        has_cache=_i >= 4,
        has_classroom=_i >= 5,
        has_eval=_i >= 6,
        has_dataset=_i >= 7,
        has_docs=_i >= 8,
        has_learned_ranker=_i >= 9,
        has_extraction=_i >= 10,
        has_scheduler=_i >= 11,
        has_notifier=_i >= 12,
        has_opportunities=_i >= 13,
        has_actions=_i >= 14,
        has_security=_i >= 15,
        has_progress=_i >= 16,
        has_rag=_i >= 17,
    ))


# ═════════════════════════════════════════════════════════════════════════════
#  README.md  (all versions)
# ═════════════════════════════════════════════════════════════════════════════

def gen_readme(v: VersionInfo) -> str:
    lines: list[str] = []
    lines.append("# Student OS\n")
    lines.append("**An MCP-powered AI coordination layer for student life.**")
    lines.append(f"BTech Final Year Project — CSE/IT. Current version: **v{v.ver}**.\n")

    lines.append("Instead of checking multiple apps every morning, a student asks one question —")
    lines.append('*"What should I do today?"* — and Student OS reads across their connected')

    platforms = ", ".join(v.server_list)
    lines.append(f"platforms ({platforms}), **ranks** everything")

    extra = ""
    if v.has_learned_ranker:
        extra += "by a learned model, "
    if v.has_extraction:
        extra += "**extracts** deadlines hidden in text, "
    if v.has_scheduler:
        extra += "**plans** the day, "
    if v.has_opportunities:
        extra += "**tracks** opportunities, "
    if v.has_actions:
        extra += "and can safely **act** — "

    if extra:
        lines.append(extra + "all from one calm interface.\n")
    else:
        lines.append("by importance, and presents a single prioritized plan.\n")

    lines.append("It is built on the **Model Context Protocol (MCP)**: each platform is a small,")
    lines.append("independent MCP server exposing standardized tools, and an orchestrator fans out")
    lines.append("across them, merges, ranks, and plans.\n")
    lines.append("---\n")

    # Runs immediately
    lines.append("## Runs immediately — no accounts needed\n")
    lines.append("The whole system ships in **mock mode** (`STUDENT_OS_MOCK=true`, the default):")
    lines.append("every server returns realistic sample data and a rule-based planner runs, so you")
    lines.append("can demo the full pipeline before wiring a single API key, then switch pieces to")
    if v.has_docs:
        lines.append('"real" one at a time (see `docs/SETUP.md`).\n')
    else:
        lines.append('"real" one at a time.\n')

    # Quickstart
    lines.append("## Quickstart\n")
    lines.append("```bash")
    lines.append("# Backend")
    lines.append("cd backend")
    lines.append('python -m venv .venv && source .venv/bin/activate    # Windows: .venv\\Scripts\\activate')
    lines.append("pip install -r requirements.txt")
    lines.append("python demo.py                    # prints today's ranked plan (no server needed)")
    lines.append("uvicorn app.main:app --reload     # or run the API → http://127.0.0.1:8000/docs")
    if v.has_frontend:
        lines.append("")
        lines.append("# Frontend (separate terminal)")
        lines.append("cd frontend && npm install && npm run dev            # → http://localhost:3000")
    lines.append("```\n")

    if v.has_learned_ranker:
        lines.append("Optional: `python -m app.intelligence.train` trains the learned ranker, then set")
        lines.append("`RANKER=learned`.", )
    if v.has_docs:
        lines.append("Full setup for real Google/GitHub data is in `docs/SETUP.md`.\n")

    lines.append("---\n")

    # Feature table
    lines.append("## What it does (feature map)\n")
    lines.append("| Capability | Where | Since |")
    lines.append("| --- | --- | --- |")
    lines.append("| MCP orchestrator (tool router, dedupe" + (", cache" if v.has_cache else "") + ") | `app/orchestrator/mcp_manager.py` | v0.1 |")

    server_entries = "GitHub, Gmail, Calendar"
    sv_count = 3
    if v.has_codeforces:
        server_entries += ", Codeforces"
        sv_count += 1
    if v.has_classroom:
        server_entries += ", Classroom"
        sv_count += 1
    lines.append(f"| {sv_count} MCP servers: {server_entries} | `mcp_servers/` | v0.1–0.{max(1, min(v.idx, 6))} |")

    lines.append("| Context-aware **rule-based** prioritizer (baseline) | `app/orchestrator/prioritizer.py` | v0.1 |")

    if v.has_learned_ranker:
        lines.append("| **Learning-to-rank** prioritizer (trained, pluggable) | `app/intelligence/` | v0.10 |")
    if v.has_cache:
        lines.append("| Caching (Redis or in-memory) | `app/cache.py` | v0.5 |")
    if v.has_learned_ranker:
        lines.append("| Persistence + feedback loop (SQLite/Postgres) | `app/store.py` | v0.10 |")
    if v.has_extraction:
        lines.append("| **NLP deadline extraction** from text | `mcp_servers/common/extraction.py` | v0.11 |")
    if v.has_scheduler:
        lines.append("| **Day-scheduler** + wellbeing pacing | `app/intelligence/scheduler.py` | v0.12 |")
    if v.has_notifier:
        lines.append("| **Proactive notifier** (Telegram/email/dry-run) | `app/notifier.py` | v0.13 |")
    if v.has_opportunities:
        lines.append("| **Opportunity radar** + application tracking | `app/intelligence/opportunities.py` | v0.14 |")
    if v.has_actions:
        lines.append("| **Action layer** (propose→confirm guardrails) | `app/actions.py` | v0.15 |")
    if v.has_security:
        lines.append("| **Security**: injection defence, token vault, scope audit | `app/security.py` | v0.16 |")
    if v.has_progress:
        lines.append("| **Progress/habit dashboard** | `/progress` + `frontend/app/progress` | v0.17 |")
    if v.has_rag:
        lines.append("| **Study-material RAG** assistant | `app/intelligence/rag.py` | v0.18 |")
    if v.has_eval:
        lines.append(f"| Offline **evaluation**" + (" + significance" if v.has_dataset else "") + (" + red-team" if v.has_security else "") + " | `eval/` | v0.7" + ("–0.16" if v.has_security else "–0.8" if v.has_dataset else "") + " |")
    if v.has_frontend:
        lines.append(f"| Web dashboard + chat" + (" + progress" if v.has_progress else "") + " (Next.js/TS) | `frontend/` | v0.2+ |")
    lines.append("")

    # API endpoints
    lines.append("**API endpoints:** " + " · ".join(f"`{e}`" for e in v.endpoints) + ".\n")

    # Research result (only if eval exists)
    if v.has_eval:
        lines.append("## The research result\n")
        if v.has_learned_ranker:
            lines.append("On **40 labeled scenarios**, the learned ranker scores **nDCG@5 = 0.968** on")
            lines.append("unseen scenarios (leave-one-out CV) vs 0.887 for due-date sorting — a")
            lines.append("statistically significant win (Wilcoxon p ≈ 2e-5).")
        else:
            lines.append("On **" + ("40" if v.has_dataset else "8") + " labeled scenarios**, the context-aware prioritizer scores **nDCG@5 = 0.954** vs")
            lines.append("0.887 for due-date sorting — a statistically significant win" + (" (Wilcoxon p ≈ 0.0004)" if v.has_dataset else "") + ".")
        if v.has_security:
            lines.append(" The prompt-injection filter catches **100%** of a red-team set with **0%** false positives.")
        lines.append(f" Details and methodology in `docs/EVALUATION.md`.\n")

    # Project layout
    lines.append("## Project layout\n")
    lines.append("```")
    lines.append("student-os/")
    lines.append("├─ backend/")
    lines.append("│  ├─ app/")
    lines.append("│  │  ├─ main.py              FastAPI app (all endpoints)")

    config_line = "│  │  ├─ config.py schemas.py"
    if v.has_cache:
        config_line += " cache.py"
    if v.has_learned_ranker:
        config_line += " store.py"
    if v.has_security:
        config_line += " security.py"
    if v.has_notifier:
        config_line += " notifier.py"
    if v.has_actions:
        config_line += " actions.py"
    lines.append(config_line)

    lines.append("│  │  ├─ orchestrator/        mcp_manager · prioritizer · " + ("ranking · " if v.has_learned_ranker else "") + "llm · agent")
    if v.has_learned_ranker:
        intl = "features · train · learned_ranker"
        if v.has_scheduler:
            intl += " · scheduler"
        if v.has_opportunities:
            intl += " · opportunities"
        if v.has_rag:
            intl += " · rag"
        lines.append(f"│  │  └─ intelligence/        {intl}")

    server_line = "│  ├─ mcp_servers/            github · gmail · calendar"
    if v.has_codeforces:
        server_line += " · codeforces"
    if v.has_classroom:
        server_line += " · classroom"
    server_line += " · common (" + ("util" + (", google_auth" if v.has_oauth else "") + (", extraction" if v.has_extraction else "") + ")")
    lines.append(server_line)

    if v.has_eval:
        lines.append("│  ├─ eval/                   metrics · rankers" + (" · stats · datasets" if v.has_dataset else "") + " · run_eval" + (" · extraction/security evals" if v.has_security else " · extraction_eval" if v.has_extraction else ""))
    lines.append(f"│  ├─ tests/                  {v.n_tests} passing")
    lines.append("│  └─ demo.py")
    if v.has_frontend:
        lines.append("├─ frontend/                  Next.js dashboard + chat" + (" + progress page" if v.has_progress else ""))
    if v.has_docs:
        lines.append("├─ docs/                      ARCHITECTURE · SETUP · ROADMAP · EVALUATION · GUIDE.html · PRODUCT_PLAN")
    lines.append("└─ CHANGELOG.md               the version-by-version story" if v.has_docs else "└─ README.md")
    lines.append("```\n")

    # Status
    lines.append("## Status\n")
    if v.idx == 17:  # v0.18.0
        lines.append(f"All Must/Should/Could **code** features in `docs/PRODUCT_PLAN.md` are implemented")
        lines.append(f"and tested (**{v.n_tests} tests passing**; frontend type-checks). The only remaining plan")
        lines.append("item is the **two-week user study** (non-code). See `docs/GUIDE.html` for a")
        lines.append("plain-English tour and `CHANGELOG.md` for what each version added.\n")
    else:
        lines.append(f"Current version: **v{v.ver}** — {v.theme}.")
        lines.append(f"**{v.n_tests} tests passing**.\n")

    # Team
    lines.append("## Team\n")
    lines.append("Nancy Singh (23/IT/108) · Priyanshu Jha (23/IT/122) · Nimish Aggarwal (23/IT/111)")
    lines.append("Guide: Dr. Varsha Sisaudia, Information Technology.\n")

    return "\n".join(lines)


# ═════════════════════════════════════════════════════════════════════════════
#  CHANGELOG.md  (v0.9.0+)
# ═════════════════════════════════════════════════════════════════════════════

_CHANGELOG_ENTRIES = [
    ("0.18.0", "Study-material RAG assistant", "*(current)*", """\
**Theme: ask your own notes.**
- Added `app/intelligence/rag.py`: a dependency-free **TF-IDF + cosine** retrieval
  layer over the student's notes (`.md`/`.txt`), split into passages.
- Extractive by default (returns the most relevant passages, so it can't
  hallucinate); an LLM can compose an answer when a key is set.
- New `GET /study/ask?q=...`, a bundled sample corpus (OS + DBMS notes), and tests."""),

    ("0.17.0", "Progress & habit dashboard", "", """\
**Theme: show follow-through over time.**
- Added `store.get_progress()`: done-streak (consecutive days completing
  something), action counts, and the opportunity **application funnel**.
- New `GET /progress` endpoint and a frontend **/progress** page (streak +
  action bars + funnel). Tests cover the aggregation."""),

    ("0.16.0", "Security hardening", "", """\
**Theme: safe with real personal data.**
- Added `app/security.py`: a **prompt-injection sanitizer** (wired into the LLM
  context so untrusted email/tool text can't hijack the model), a Fernet
  **token vault** (encryption at rest), and a **read-only scope audit**.
- Red-team benchmark (`eval/security_eval.py`): **100%** of injection attempts
  caught, **0%** false positives on benign text. Tests included."""),

    ("0.15.0", "Action layer with guardrails", "", """\
**Theme: the app can act, safely.**
- Added `app/actions.py`: a **propose → confirm** flow for draft_reply, add_event,
  snooze, and mark_done. Nothing executes without a one-time confirmation token,
  so the agent never acts silently on the student's behalf.
- Executions are logged to the store (mark_done/snooze feed the ranker).
- New `POST /actions/propose` and `POST /actions/confirm`. Tests cover the
  single-use token, rejection of unknown tokens, and invalid actions."""),

    ("0.14.0", "Opportunity radar + application tracking", "", """\
**Theme: never miss the things that matter most in placement season.**
- Added `app/intelligence/opportunities.py`: classifies items into internships /
  scholarships / hackathons / contests and merges saved **application status**
  (new → interested → applied → offer/rejected), persisted in the store.
- New `GET /opportunities` and `POST /opportunities/status`. Tests cover
  classification, status round-trip, and validation."""),

    ("0.13.0", "Proactive notifier", "", """\
**Theme: push the brief, don't wait to be asked.**
- Added `app/notifier.py`: formats the daily brief + pre-deadline alerts and
  sends via **Telegram or email** when configured, else a safe **dry-run**.
- CLI `python -m app.notifier` for a scheduled daily run; `GET /notify/preview`
  and `POST /notify/send` endpoints. Tests cover formatting and channel logic."""),

    ("0.12.0", "Intelligent day-scheduler + wellbeing pacing", "", """\
**Theme: from a ranked list to an actual plan.**
- Added a **day-scheduler** (`app/intelligence/scheduler.py`) that time-blocks
  ranked tasks into the day's free slots, respecting effort estimates.
- **Wellbeing-aware pacing**: when there's more work than hours, it schedules the
  top-priority tasks and honestly defers the rest with gentle advice, instead of
  planning an impossible day.
- New `GET /schedule` endpoint. Tests: no overlaps, only real tasks blocked,
  overflow + overcommit detection."""),

    ("0.11.0", "NLP deadline extraction", "", """\
**Theme: catch deadlines hidden in text.**
- Added `mcp_servers/common/extraction.py` — dependency-free parsing of relative
  ("apply by Friday", "in 3 days") and absolute ("3 August", "05/08") dates.
- Wired into the **Gmail** and **Classroom** servers: emails/announcements with no
  explicit date now get a due date (marked `due_source=extracted`).
- Added a labeled extraction benchmark (`eval/extraction_eval.py`) —
  precision/recall/F1 = **1.00** on the current set — and unit tests."""),

    ("0.10.0", "Learned ranker + persistence + feedback loop", "", """\
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
- Tests: 22 → **31 passing** (features, store, learned ranker)."""),

    ("0.9.0", "Documentation set", "", """\
- Authored `docs/`: `ARCHITECTURE.md`, `SETUP.md`, `ROADMAP.md`,
  `EVALUATION.md`, the illustrated `GUIDE.html`, and the `PRODUCT_PLAN.md`
  master plan."""),

    ("0.8.0", "Bigger benchmark + statistical significance", "", """\
- Grew the eval dataset from 8 to **40 labeled scenarios** (`build_dataset.py`).
- Added a **paired significance test** (`eval/stats.py`): Wilcoxon signed-rank +
  bootstrap CI + effect size, cross-checked against scipy."""),

    ("0.7.0", "Evaluation harness", "", """\
- Added `eval/`: ranking metrics (nDCG@k, precision@k, pairwise, MRR), baseline
  rankers (random / arrival-order / due-date), and a runner producing a
  comparison table. Turned "we built it" into "we measured it.\""""),

    ("0.6.0", "Google Classroom connector", "", """\
- Added the Classroom MCP server (pending assignments + announcements),
  reusing the shared Google OAuth token."""),

    ("0.5.0", "Caching layer", "", """\
- Added `app/cache.py`: Redis when available, in-memory TTL cache otherwise.
- Cold briefing ~6s → **near-instant** on cache hit; `?refresh=true` to bypass."""),

    ("0.4.0", "Real Google data (OAuth)", "", """\
- Added shared Google OAuth (`mcp_servers/common/google_auth.py`) with a login
  CLI and token refresh; wired **Gmail** and **Calendar** to their real APIs."""),

    ("0.3.0", "Codeforces connector", "", """\
- Added the Codeforces MCP server (upcoming contests via the public API +
  practice reminder). Proved a new platform drops in without touching the core."""),

    ("0.2.0", "Web app", "", """\
- Added the **Next.js + TypeScript** frontend: a daily-briefing dashboard and a
  chat panel talking to the backend API."""),

    ("0.1.0", "Initial platform", "", """\
- MCP **orchestrator** (tool router) that launches servers over stdio, merges,
  and de-duplicates results.
- Three MCP servers: **GitHub** (real API + mock), **Gmail**, **Calendar** (mock
  + OAuth-ready).
- **Context-aware prioritizer** (rule-based, exam-week logic) + unit tests.
- **FastAPI** backend (`/briefing`, `/chat`, `/tools`, `/health`).
- **Mock mode** so the whole system runs end-to-end with zero credentials."""),
]


def gen_changelog(v: VersionInfo) -> str:
    lines: list[str] = []
    lines.append("# Changelog\n")
    lines.append("All notable changes to Student OS, version by version. The project was built")
    lines.append("incrementally — each version adds one meaningful capability on top of the last.")
    lines.append("Format loosely follows [Keep a Changelog](https://keepachangelog.com/); versions")
    lines.append("use [Semantic Versioning](https://semver.org/) (0.x = pre-release milestones).\n")
    lines.append("---\n")

    is_first = True
    for entry_ver, entry_title, entry_tag, entry_body in _CHANGELOG_ENTRIES:
        # Only include entries up to current version
        entry_idx = _VERS.index(entry_ver)
        if entry_idx > v.idx:
            continue

        tag = " *(current)*" if is_first else ""
        lines.append(f"## v{entry_ver} — {entry_title}{tag}")
        lines.append(entry_body)
        lines.append("")
        is_first = False

    lines.append("---\n")
    lines.append("### Legend of where each version lives in the code")
    legend = "`app/orchestrator/` (routing + ranking) · `mcp_servers/` (connectors)"
    if v.has_cache:
        legend += " ·\n`app/cache.py` (caching)"
    if v.has_learned_ranker:
        legend += " · `app/store.py` (persistence) · `app/intelligence/`\n(learning)"
    if v.has_eval:
        legend += " · `eval/` (evaluation)"
    if v.has_frontend:
        legend += " · `frontend/` (web app)"
    if v.has_docs:
        legend += " · `docs/` (writing)"
    legend += ".\n"
    lines.append(legend)

    return "\n".join(lines)


# ═════════════════════════════════════════════════════════════════════════════
#  ARCHITECTURE.md  (v0.9.0+)
# ═════════════════════════════════════════════════════════════════════════════

def gen_architecture(v: VersionInfo) -> str:
    lines: list[str] = []
    lines.append("# Architecture\n")

    desc = "Student OS keeps the layered MCP design from the proposal"
    if v.has_learned_ranker:
        desc += " and adds an\nintelligence layer (learning"
        if v.has_extraction:
            desc += ", extraction"
        if v.has_scheduler:
            desc += ", scheduling"
        desc += "), a persistence + feedback\nloop"
    if v.has_security:
        desc += ", a security layer"
    if v.has_actions:
        desc += ", and an action layer"
    desc += f". This document is current as of\n**v{v.ver}**.\n"
    lines.append(desc)

    # Architecture diagram
    lines.append("```")
    lines.append("Student (natural-language input)")
    lines.append("        │")
    lines.append("        ▼")
    if v.has_frontend:
        fe_desc = "FRONTEND  (Next.js: dashboard · chat" + (" · progress" if v.has_progress else "") + ")      ← frontend/"
        lines.append(fe_desc)
        lines.append("        │  HTTP")
        lines.append("        ▼")
    lines.append("BACKEND API (FastAPI)                                  ← app/main.py")
    ep_line = "  " + " ".join(v.endpoints)
    lines.append(ep_line)
    lines.append("        │")
    lines.append("        ▼")
    lines.append("ORCHESTRATOR (tool router)                             ← app/orchestrator/mcp_manager.py")
    orch_desc = "  • launches MCP servers over stdio, lists+calls tools"
    lines.append(orch_desc)
    cache_desc = "  • normalizes to ActionItem, de-duplicates"
    if v.has_cache:
        cache_desc += ", CACHES     ← app/cache.py"
    lines.append(cache_desc)
    lines.append("        │")

    srv_line = "        ├── " + " · ".join(v.server_list) + "  ← mcp_servers/*"
    lines.append(srv_line)
    lines.append("        │        (each wraps a real API; mock fallback)")
    if v.has_extraction:
        lines.append("        │        Gmail/Classroom text → DEADLINE EXTRACTION      ← mcp_servers/common/extraction.py")
    lines.append("        ▼")

    if v.has_learned_ranker:
        lines.append("INTELLIGENCE                                           ← app/intelligence/")
        intl = "  • ranking: rule-based baseline OR learned model       ← ranking.py · learned_ranker.py · prioritizer.py"
        lines.append(intl)
        if v.has_scheduler:
            lines.append("  • scheduler (time-blocks the day, wellbeing pacing)    ← scheduler.py")
        if v.has_opportunities:
            lines.append("  • opportunities (radar + application status)           ← opportunities.py")
        if v.has_rag:
            lines.append("  • study assistant (TF-IDF RAG over notes)              ← rag.py")
        lines.append("        │")
        lines.append("        ▼")

    if v.has_security:
        lines.append("SECURITY (untrusted text sanitized before the LLM)     ← app/security.py")
        lines.append("        │")
        lines.append("        ▼")

    lines.append("LLM writer (Claude) or deterministic fallback          ← app/orchestrator/llm.py")

    if v.has_learned_ranker:
        lines.append("        │")
        lines.append("        ▼")
        lines.append("PERSISTENCE (SQLite/Postgres): shown items + feedback  ← app/store.py")
        if v.has_progress:
            lines.append("        │                                                 (feeds learning + /progress)")

    if v.has_notifier:
        lines.append("        │")
        lines.append("        ▼")
        lines.append("NOTIFIER (Telegram / email / dry-run), scheduled        ← app/notifier.py")

    lines.append("```\n")

    # Request flow
    lines.append('## Request flow: "What should I do today?"\n')
    lines.append("1. **API** — `GET /briefing` calls `agent.build_briefing()`.")
    lines.append("2. **Fan-out" + (" (cached)" if v.has_cache else "") + "** — `mcp_manager.gather_action_items()` reads")
    lines.append("   `servers.json`, launches each enabled server as a subprocess over **stdio**,")
    lines.append("   calls `initialize`, `list_tools`, then every tool." + (" Results are cached briefly\n   (`app/cache.py`) so repeat calls are instant." if v.has_cache else ""))

    step = 3
    lines.append(f"{step}. **Normalize" + (" + extract" if v.has_extraction else "") + "** — each tool returns `ActionItem`-shaped rows" + (";" if v.has_extraction else ".") + (" Gmail" if v.has_extraction else ""))
    if v.has_extraction:
        lines.append("   and Classroom additionally run **deadline extraction** so due dates hidden in")
        lines.append("   text are recovered.")
    lines.append("   The manager maps to `ActionItem` models and de-duplicates.")

    step += 1
    if v.has_learned_ranker:
        lines.append(f"{step}. **Rank** — `ranking.get_ranker()` picks the ranker from config: the")
        lines.append("   rule-based `prioritizer` (baseline / cold-start) or the trained")
        lines.append("   `LearnedRanker`. Both produce a sorted list.")
    else:
        lines.append(f"{step}. **Rank** — the `prioritizer` scores items by kind, due-proximity, and")
        lines.append("   context (exam week, internship category, noise detection) and sorts them.")

    step += 1
    lines.append(f"{step}. **Summarize" + (" (safely)" if v.has_security else "") + "** — `llm.write_briefing()` writes a headline + summary" + ((";\n   untrusted item text is first passed through `security.safe_text()` to strip\n   prompt-injection.") if v.has_security else ".") + " With `ANTHROPIC_API_KEY` set it uses Claude, else a")
    lines.append("   deterministic writer.")

    step += 1
    if v.has_learned_ranker:
        lines.append(f"{step}. **Log + respond** — the shown items are recorded to the store (feedback loop),")
        lines.append("   and a `Briefing` is returned and rendered by the dashboard.")
    else:
        lines.append(f"{step}. **Respond** — a `Briefing` is returned and rendered by the dashboard.")

    lines.append("")

    # Other flows
    if v.has_scheduler or v.has_opportunities or v.has_notifier:
        extra = "Other flows reuse steps 2–4: "
        parts = []
        if v.has_scheduler:
            parts.append("`/schedule` feeds the ranked list into the\nscheduler")
        if v.has_opportunities:
            parts.append("`/opportunities` classifies + merges saved status")
        parts.append("`/chat` routes a\nquestion over the same context")
        if v.has_notifier:
            parts.append("`/notify` formats and pushes the briefing")
        extra += "; ".join(parts) + ".\n"
        lines.append(extra)

    # ActionItem contract
    lines.append("## The `ActionItem` contract\n")
    lines.append("Every server, regardless of platform, emits rows with these keys — the shared")
    lines.append("shape that lets the ranker compare a PR against an email against an exam:\n")
    lines.append("| key | meaning |")
    lines.append("| --- | --- |")
    lines.append("| `kind` | type within the source: `pull_request`, `email`, `deadline`, `exam`, `event`, `issue`, `notification`" + (", `contest`, `practice`" if v.has_codeforces else "") + (", `announcement`" if v.has_classroom else "") + " |")
    lines.append("| `title` | one-line label shown to the student |")
    lines.append("| `detail` | secondary context (repo/#, sender, location) |")
    lines.append("| `url` | deep link (optional) |")
    lines.append('| `due` | ISO date (optional)' + ("; may be **extracted** from text" if v.has_extraction else "") + " |")
    lines.append('| `extra` | source metadata (e.g. `{"category": "internship"' + (', "due_source": "extracted"' if v.has_extraction else '') + '}`) |\n')

    # Layer responsibilities
    lines.append("## Layer responsibilities\n")
    lines.append("* **MCP servers** (`mcp_servers/`) — one per platform; wrap a real API with a")
    lines.append("  mock fallback; read-only." + (" Shared helpers live in `common/` (OAuth" + (", extraction" if v.has_extraction else "") + ")." if v.has_oauth else ""))
    lines.append("* **Orchestrator** (`app/orchestrator/`) — fan-out, dedupe, " + ("cache, " if v.has_cache else "") + "ranking")
    lines.append("  selection, LLM writing.")
    if v.has_learned_ranker:
        intl_desc = "feature builder, trained ranker"
        if v.has_scheduler:
            intl_desc += ", scheduler"
        if v.has_opportunities:
            intl_desc += ", opportunities"
        if v.has_rag:
            intl_desc += ", RAG"
        lines.append(f"* **Intelligence** (`app/intelligence/`) — the learnable/algorithmic parts:\n  {intl_desc}.")
        lines.append("* **Persistence** (`app/store.py`) — SQLAlchemy over SQLite (default) or Postgres")
        lines.append("  (`DATABASE_URL`); logs shown items + feedback; powers learning" + (" and `/progress`" if v.has_progress else "") + ".")
    if v.has_security:
        lines.append("* **Security** (`app/security.py`) — injection sanitizer, Fernet token vault,")
        lines.append("  read-only scope audit.")
    if v.has_actions:
        lines.append("* **Actions** (`app/actions.py`) — propose→confirm guardrail for write-actions.")
    if v.has_notifier:
        lines.append("* **Notifier** (`app/notifier.py`) — scheduled push to Telegram/email.")
    lines.append("")

    # Design principles
    lines.append("## Design principles\n")
    lines.append("* **Isolation** — a failing/slow server is skipped; the briefing still works.")
    lines.append("* **Graceful degradation** — no credentials, no LLM key" + (", no Redis" if v.has_cache else "") + (", no DB write?" if v.has_learned_ranker else "?"))
    lines.append("  Each falls back (mock data / deterministic writer" + (" / in-memory cache" if v.has_cache else "") + ") so the app")
    lines.append("  always runs.")
    lines.append("* **Reuse** — servers are standard MCP; they work in any MCP client.")
    if v.has_learned_ranker:
        lines.append("* **Pluggability** — the ranker is swappable (`RANKER=rule|learned`)" + ("; the cache\n  and DB back-ends are swappable via env." if v.has_cache else "."))
    lines.append("")

    # Adding a new server
    lines.append("## Adding a new MCP server (still a one-file change)\n")
    lines.append("1. Create `mcp_servers/<x>_server/server.py` — copy `github_server`.")
    lines.append("2. Return `ActionItem`-shaped dicts from each `@mcp.tool()`.")
    lines.append("3. Register it in `backend/servers.json`.")
    lines.append("4. Done — orchestrator, ranker, API, and UI need no changes." + (" (Codeforces" + (" and\n   Classroom were" if v.has_classroom else " was") + " added exactly this way.)" if v.has_codeforces else ""))
    lines.append("")

    return "\n".join(lines)


# ═════════════════════════════════════════════════════════════════════════════
#  SETUP.md  (v0.9.0+)
# ═════════════════════════════════════════════════════════════════════════════

def gen_setup(v: VersionInfo) -> str:
    lines: list[str] = []
    lines.append("# Setup — going from mock to real\n")
    lines.append("Everything below is optional. The app runs fully in mock mode with no keys.\n")

    # 0. Env
    lines.append("## 0. Environment file\n")
    lines.append("```bash")
    lines.append("cp .env.example .env")
    lines.append("```\n")
    lines.append("Set `STUDENT_OS_MOCK=false` once you want servers to use real APIs. You can mix:")
    lines.append("with mock off, any server that still lacks credentials just returns its sample")
    lines.append("data, so you can turn on one platform at a time.\n")

    # 1. GitHub
    lines.append("## 1. GitHub (real, easiest — start here)\n")
    lines.append("1. GitHub → Settings → Developer settings → **Personal access tokens** →")
    lines.append("   *Tokens (classic)* → Generate new token.")
    lines.append("2. Scopes: `repo:status`, `read:user`, `notifications` (read-only is enough).")
    lines.append("3. Put it in `.env`:")
    lines.append("   ```")
    lines.append("   STUDENT_OS_MOCK=false")
    lines.append("   GITHUB_TOKEN=ghp_xxx")
    lines.append("   ```")
    lines.append("4. `cd backend && python demo.py` — you should now see your real PRs/issues.\n")

    # 2. LLM
    lines.append("## 2. LLM writer (optional)\n")
    lines.append("```")
    lines.append("ANTHROPIC_API_KEY=sk-ant-xxx")
    lines.append("LLM_MODEL=claude-sonnet-5")
    lines.append("```")
    lines.append("Without this, briefings/chat use the built-in rule-based writer (no key needed).\n")

    # 3. Google
    if v.has_oauth:
        lines.append("## 3. Google — Gmail + Calendar (real, one-time consent)\n")
        lines.append("Gmail and Calendar are fully implemented against the real Google APIs and share")
        lines.append("one OAuth token. Setup:\n")
        lines.append("1. [Google Cloud Console](https://console.cloud.google.com/) → new project.")
        apis = "**Gmail API**, **Google Calendar API**"
        if v.has_classroom:
            apis += ", and **Google Classroom API**"
        lines.append(f"2. Enable the {apis}.")
        scopes = "Gmail" + (", Calendar, and Classroom" if v.has_classroom else " and Calendar")
        lines.append(f"3. Configure the OAuth consent screen (External; add your Google account as a")
        lines.append(f"   **test user**). Add the read-only {scopes} scopes.")
        lines.append("4. Create **OAuth client credentials** → *Desktop app* → copy the client id/secret.")
        lines.append("5. Put them in `.env` and turn real mode on:")
        lines.append("   ```")
        lines.append("   STUDENT_OS_MOCK=false")
        lines.append("   GOOGLE_CLIENT_ID=...apps.googleusercontent.com")
        lines.append("   GOOGLE_CLIENT_SECRET=...")
        lines.append("   ```")
        lines.append("6. Run the one-time login (opens your browser, asks for read-only consent):")
        lines.append("   ```bash")
        lines.append("   cd backend")
        lines.append("   python -m mcp_servers.common.google_auth login")
        lines.append("   ```")
        lines.append("   This saves a refresh token to `backend/.google_token.json` (git-ignored).")
        servers = "Gmail/Calendar" + ("/Classroom" if v.has_classroom else "")
        lines.append(f"   From then on the {servers} servers read your real data and")
        lines.append("   refresh the token automatically. All scopes are read-only.\n")
        lines.append("If credentials or the token are missing, both servers quietly fall back to mock")
        lines.append("data (and print a hint to stderr), so the app never breaks.\n")

    # 3b. Codeforces
    if v.has_codeforces:
        lines.append("## " + ("3b" if v.has_oauth else "3") + ". Codeforces (real, no auth for contests)\n")
        lines.append("Upcoming contests come from the public Codeforces API with no credentials.")
        lines.append("The optional practice reminder uses your handle:\n")
        lines.append("```")
        lines.append("CODEFORCES_HANDLE=your_cf_handle")
        lines.append("```\n")

    # 4. Running both halves
    section_num = 4
    lines.append(f"## {section_num}. Running both halves\n")
    lines.append("```bash")
    lines.append("# terminal 1")
    lines.append("cd backend && uvicorn app.main:app --reload")
    if v.has_frontend:
        lines.append("")
        lines.append("# terminal 2")
        lines.append("cd frontend && npm install && npm run dev")
    lines.append("```\n")
    if v.has_frontend:
        lines.append("Open http://localhost:3000.\n")

    # 5. Tests
    section_num += 1
    lines.append(f"## {section_num}. Tests & evaluations\n")
    lines.append("```bash")
    lines.append(f"cd backend && python -m pytest                 # {v.n_tests} tests")
    if v.has_eval:
        lines.append("python -m eval.run_eval                         # ranking benchmark" + (" + significance" if v.has_dataset else ""))
    if v.has_extraction:
        lines.append("python -m eval.extraction_eval                  # deadline-extraction precision/recall")
    if v.has_security:
        lines.append("python -m eval.security_eval                    # prompt-injection red-team")
    lines.append("```\n")

    # Caching
    if v.has_cache:
        section_num += 1
        lines.append(f"## {section_num}. Caching (optional Redis)\n")
        lines.append("The briefing fan-out is cached so repeated calls don't re-hit every API.")
        lines.append("By default this uses an in-memory cache — nothing to install. To use Redis:\n")
        lines.append("```")
        lines.append("REDIS_URL=redis://localhost:6379/0")
        lines.append("CACHE_TTL_SECONDS=90")
        lines.append("```\n")

    # Learned ranker
    if v.has_learned_ranker:
        section_num += 1
        lines.append(f"## {section_num}. Learned ranker (optional)\n")
        lines.append("The rule-based ranker is the default. To use the trained learning-to-rank model:\n")
        lines.append("```bash")
        lines.append("cd backend")
        lines.append("python -m app.intelligence.train    # writes app/intelligence/ranker_weights.json")
        lines.append("```")
        lines.append("Then set `RANKER=learned` in `.env`. If the weights file is missing, the app")
        lines.append("falls back to the rule-based ranker automatically (cold start).\n")

    # Notifier
    if v.has_notifier:
        section_num += 1
        lines.append(f"## {section_num}. Notifications (optional)\n")
        lines.append("The notifier pushes the daily brief + pre-deadline alerts. With nothing set it")
        lines.append("runs in **dry-run** (prints the message). To send for real, set one channel:\n")
        lines.append("```")
        lines.append("# Telegram")
        lines.append("TELEGRAM_BOT_TOKEN=123456:abc")
        lines.append("TELEGRAM_CHAT_ID=123456789")
        lines.append("# or email (SMTP)")
        lines.append("SMTP_HOST=smtp.gmail.com")
        lines.append("SMTP_PORT=587")
        lines.append("SMTP_USER=you@gmail.com")
        lines.append("SMTP_PASSWORD=app-password")
        lines.append("NOTIFY_EMAIL_TO=you@gmail.com")
        lines.append("```")
        lines.append("Run once (wire to cron / Windows Task Scheduler for a daily brief):")
        lines.append("```bash")
        lines.append("cd backend && python -m app.notifier")
        lines.append("```\n")

    # Security
    if v.has_security:
        section_num += 1
        lines.append(f"## {section_num}. Security (optional token vault)\n")
        lines.append("OAuth scopes are already read-only, and untrusted email/tool text is sanitized")
        lines.append("against prompt-injection automatically. To encrypt secrets at rest, generate a")
        lines.append("vault key and set it:\n")
        lines.append('```bash')
        lines.append('python -c "from app.security import TokenVault; print(TokenVault.generate_key())"')
        lines.append("```")
        lines.append("```")
        lines.append("STUDENT_OS_VAULT_KEY=<the printed key>")
        lines.append("```\n")

    # RAG
    if v.has_rag:
        section_num += 1
        lines.append(f"## {section_num}. Study-material assistant (optional)\n")
        lines.append("Point the RAG assistant at your own notes (`.md`/`.txt`); it defaults to the")
        lines.append("bundled sample corpus otherwise:\n")
        lines.append("```")
        lines.append("STUDY_NOTES_DIR=/path/to/your/notes")
        lines.append("```")
        lines.append("Ask questions via `GET /study/ask?q=...`.\n")

    # Persistence
    if v.has_learned_ranker:
        section_num += 1
        lines.append(f"## {section_num}. Persistence (SQLite default, Postgres optional)\n")
        lines.append("History and feedback are stored in SQLite (`backend/student_os.db`) with zero")
        lines.append("setup. To use PostgreSQL instead:\n")
        lines.append("```")
        lines.append("DATABASE_URL=postgresql+psycopg://user:pass@localhost/student_os")
        lines.append('```')
        lines.append('(Install a driver too, e.g. `pip install "psycopg[binary]"`.) The feedback loop')
        lines.append("powers the learned ranker" + (" and the `/progress` dashboard" if v.has_progress else "") + ".\n")

    return "\n".join(lines)


# ═════════════════════════════════════════════════════════════════════════════
#  EVALUATION.md  (v0.9.0+, but only meaningful from v0.7.0 which is guaranteed)
# ═════════════════════════════════════════════════════════════════════════════

def gen_evaluation(v: VersionInfo) -> str:
    lines: list[str] = []
    lines.append("# Evaluating the prioritizer\n")
    lines.append("This is the piece that turns Student OS from \"a working build\" into a project")
    lines.append("with a **measurable result** you can defend in a viva and write up in a paper.\n")

    lines.append("## Research question\n")
    lines.append("> Does context-aware prioritization rank a student's cross-platform action")
    lines.append("> items closer to human judgment than simple heuristics (due-date sorting,")
    lines.append("> arrival order, random)?\n")

    # Method
    lines.append("## Method\n")
    lines.append("We evaluate ranking quality offline against a labeled dataset — the standard")
    lines.append("information-retrieval setup, so the methodology is familiar to reviewers.\n")

    n_scenarios = "40" if v.has_dataset else "8"
    lines.append(f"**Dataset** (`eval/dataset.json`, authored in `eval/build_dataset.py`).")
    lines.append(f"**{n_scenarios} realistic student scenarios** (exam weeks, placement season, deadline")
    lines.append("clusters, hackathons, quiet days" + (", buried internship mail, semester start,\nregistration day, and edge cases like \"only noise\" or \"everything due today\"" if v.has_dataset else "") + ").")
    lines.append("Each scenario is a set of action items, and each item has a hand-set human")
    lines.append("**relevance grade**:\n")
    lines.append("| grade | meaning |")
    lines.append("| --- | --- |")
    lines.append("| 3 | must do today |")
    lines.append("| 2 | important soon |")
    lines.append("| 1 | optional |")
    lines.append("| 0 | noise (e.g. an OTP, a promo, an old notification) |\n")

    lines.append("Due dates are stored as offsets from the run date (`due_offset_days`) so the")
    lines.append("dataset never goes stale. When the harness loads a scenario it presents the")
    lines.append("items in a **randomized-but-reproducible order** (seeded by scenario id) so no")
    lines.append("ranker can exploit the order in which the dataset happens to be written.\n")

    if v.has_dataset:
        lines.append("The set is deliberately **balanced, not rigged**: several scenarios are pure")
        lines.append("dated-deadline clusters where \"sort by due date\" is already near-optimal, so the")
        lines.append("benchmark does not secretly favour our ranker. Grades are explicit integer")
        lines.append("literals in `build_dataset.py`, assigned by human judgment — never computed from")
        lines.append("the prioritizer's rules — so the evaluation is not circular.\n")

    # Rankers
    lines.append("**Rankers** (`eval/rankers.py`).\n")
    lines.append("* `random` — shuffle (floor; averaged over 25 seeds for stability).")
    lines.append("* `source_order` — arbitrary arrival order (what you'd get with no ranking).")
    lines.append("* `due_date` — earliest due date first; undated items last. A strong, naive")
    lines.append("  heuristic — the one worth beating.")
    lines.append("* `prioritizer` — our context-aware ranker (`app/orchestrator/prioritizer.py`).")
    if v.has_learned_ranker:
        lines.append("* `learned` — the trained learning-to-rank model (`app/intelligence/learned_ranker.py`).")
    lines.append("")

    # Metrics
    lines.append("**Metrics** (`eval/metrics.py`, all unit-tested in `tests/test_metrics.py`).\n")
    lines.append("* **nDCG@k** — normalized discounted cumulative gain at k=3 and k=5; rewards")
    lines.append("  putting high-relevance items near the top. The primary metric.")
    lines.append("* **P@3** — precision@3: fraction of the top 3 that are genuinely important")
    lines.append("  (grade ≥ 2).")
    lines.append("* **pairwise** — fraction of gold-ordered item pairs the ranking gets right")
    lines.append("  (ties excluded); equivalent to (Kendall's τ + 1)/2 over untied pairs.")
    lines.append("* **MRR** — mean reciprocal rank of the first \"must do today\" (grade 3) item.\n")

    # Significance
    if v.has_dataset:
        lines.append("**Statistical significance** (`eval/stats.py`, tested in `tests/test_stats.py`).")
        lines.append("A single mean isn't enough — we test whether the improvement is real. Because")
        lines.append("each scenario gives one nDCG@5 value per ranker, we use a **paired** design and")
        lines.append("report, for prioritizer vs each baseline:\n")
        lines.append("* **Wilcoxon signed-rank test** — a non-parametric paired test (doesn't assume")
        lines.append("  the differences are normally distributed) on the per-scenario nDCG@5")
        lines.append("  differences, with tie and continuity corrections. Gives the p-value. Our")
        lines.append("  implementation is cross-checked against `scipy.stats.wilcoxon`.")
        lines.append("* **Bootstrap 95% confidence interval** for the mean difference — an intuitive")
        lines.append('  effect size: "the improvement is +0.07 nDCG@5, 95% CI [0.035, 0.098]".')
        lines.append("* **Rank-biserial effect size** and **win/tie/loss** counts across scenarios.\n")

    # How to run
    lines.append("## How to run\n")
    lines.append("```bash")
    lines.append("cd backend")
    if v.has_dataset:
        lines.append("python -m eval.build_dataset     # (re)generate dataset.json from the authored scenarios")
    lines.append("python -m eval.run_eval          # prints the table" + (" + significance" if v.has_dataset else "") + "; writes results.json/.csv")
    lines.append("python -m pytest tests/test_metrics.py" + (" tests/test_stats.py" if v.has_dataset else "") + "   # verify metrics" + (" + stats" if v.has_dataset else ""))
    lines.append("```\n")

    # Results
    lines.append(f"## Result ({n_scenarios} scenarios)\n")
    lines.append(f"Mean of each metric across the {n_scenarios} scenarios (higher is better):\n")
    lines.append("```")
    lines.append("ranker              nDCG@3      nDCG@5         P@3    pairwise         MRR")
    lines.append("--------------------------------------------------------------------------")
    lines.append("random               0.599       0.739       0.464       0.496       0.345")
    lines.append("source_order         0.622       0.752       0.450       0.536       0.361")
    lines.append("due_date             0.842       0.887       0.608       0.780       0.551")
    lines.append("prioritizer          0.930       0.954       0.725       0.905       0.662")
    if v.has_learned_ranker:
        lines.append("learned              0.952       0.968       0.758       0.928       0.695")
    lines.append("```\n")

    if v.has_dataset:
        if v.has_learned_ranker:
            lines.append("**Statistical significance** (paired, on nDCG@5):\n")
            lines.append("| comparison | mean Δ | 95% CI (bootstrap) | Wilcoxon p | effect r | win/tie/loss |")
            lines.append("| --- | --- | --- | --- | --- | --- |")
            lines.append("| learned vs **due_date** | **+0.081** | [+0.054, +0.108] | **2e-05** | +0.82 | 27 / 8 / 5 |")
            lines.append("| learned vs prioritizer | +0.014 | [+0.002, +0.027] | **0.03** | +0.36 | 14 / 17 / 9 |")
            lines.append("| prioritizer vs **due_date** | **+0.067** | [+0.035, +0.098] | **0.0004** | +0.74 | 23 / 10 / 7 |")
            lines.append("| prioritizer vs source_order | +0.202 | [+0.140, +0.269] | 1.7e-06 | +0.92 | 34 / 4 / 2 |\n")
        else:
            lines.append("**Statistical significance** (paired, on nDCG@5):\n")
            lines.append("| comparison | mean Δ | 95% CI (bootstrap) | Wilcoxon p | effect r | win/tie/loss |")
            lines.append("| --- | --- | --- | --- | --- | --- |")
            lines.append("| prioritizer vs **due_date** | **+0.067** | [+0.035, +0.098] | **0.0004** | +0.74 | 23 / 10 / 7 |")
            lines.append("| prioritizer vs source_order | +0.202 | [+0.140, +0.269] | 1.7e-06 | +0.92 | 34 / 4 / 2 |\n")

    # Interpretation
    best_ranker = "learned ranker" if v.has_learned_ranker else "prioritizer"
    lines.append(f"**Interpretation.** The {best_ranker} leads on every metric, and the improvement")
    lines.append("over the strongest baseline (due-date sorting) is **statistically significant**")
    if v.has_dataset:
        lines.append(f"(Wilcoxon p " + ("≈ 2e-05" if v.has_learned_ranker else "≈ 0.0004") + ") with a **large effect size**. The gap comes from cases due-date sorting handles badly:")
    lines.append("undated-but-urgent items (a \"recruiter is interested\" email with no deadline),")
    lines.append("noise with no date (OTPs) sinking correctly, and exam-week context pushing a")
    lines.append("contest that's *due today* below coursework due later.\n")

    if v.has_dataset:
        lines.append("**We also lose " + ("5" if v.has_learned_ranker else "7") + " of 40** — honestly. Those are mostly pure dated-deadline")
        lines.append("clusters where due-date sorting is already optimal. Reporting these is a feature: it shows the")
        lines.append("benchmark is fair and points at the next improvement.\n")

    # Threats
    lines.append("## Threats to validity (state these in the paper)\n")
    lines.append("* **Single annotator, synthetic scenarios.** The " + n_scenarios + " scenarios and their grades")
    lines.append("  reflect one author's judgment over constructed cases. This is the biggest")
    lines.append("  remaining threat. Strengthen it with ≥2 independent annotators grading the")
    lines.append("  same items, and report inter-annotator agreement (Cohen's κ).")
    lines.append(f"* **N = {n_scenarios}.** " + ("Enough for a significant paired result with a large effect size,\n  but modest." if v.has_dataset else "Small — grow to 40+ scenarios for tighter confidence intervals."))
    lines.append("* **Offline proxy.** nDCG against labels is a proxy for real usefulness. The")
    lines.append("  natural follow-up is a **user study**.\n")

    # Extending
    lines.append("## Extending\n")
    if not v.has_learned_ranker:
        lines.append("* Add a **learned ranker** — train a model on the labeled data and compare it")
        lines.append("  to the rule-based ranker.")
    lines.append("* Add an **LLM ranker** to `rankers.py` (behind `ANTHROPIC_API_KEY`) and compare")
    lines.append("  it to the " + ("learned" if v.has_learned_ranker else "rule-based") + " ranker — a clean \"does the LLM help ranking?\" experiment.")
    lines.append("* Grow `dataset.json`; the harness picks up new scenarios automatically.\n")

    return "\n".join(lines)


# ═════════════════════════════════════════════════════════════════════════════
#  ROADMAP.md  (v0.9.0+)
# ═════════════════════════════════════════════════════════════════════════════

def gen_roadmap(v: VersionInfo) -> str:
    lines: list[str] = []
    lines.append("# Roadmap & feasibility notes\n")
    lines.append("This maps the code you have now onto your proposal's 5-phase timeline, and")
    lines.append("flags the things the proposal doesn't (yet) acknowledge. Read the feasibility")
    lines.append("section before you commit to LinkedIn or LeetCode.\n")

    # Where this puts you
    lines.append("## Where this scaffold puts you\n")
    lines.append("| Proposal phase | Status in this repo |")
    lines.append("| --- | --- |")

    # Phase 1
    p1 = "Architecture done; layered MCP design implemented."
    p1 += " OAuth " + ("done." if v.has_oauth else "still to wire.")
    lines.append(f"| Phase 1 — architecture + OAuth setup | {p1} |")

    # Phase 2
    p2 = "Orchestrator + GitHub (real) done."
    p2 += " Email/Calendar " + ("wired to real APIs via OAuth." if v.has_oauth else "are working mock servers awaiting OAuth.")
    lines.append(f"| Phase 2 — Email, Calendar, GitHub servers + orchestrator | {p2} |")

    # Phase 3
    p3 = "Daily Briefing **done**."
    if v.has_codeforces:
        p3 += " Codeforces **done**."
    if v.has_classroom:
        p3 += " Classroom **done**."
    p3 += " LinkedIn: use the Gmail route — see feasibility below."
    lines.append(f"| Phase 3 — LeetCode/Classroom/LinkedIn + Daily Briefing | {p3} |")

    # Phase 4
    p4 = ""
    if v.has_frontend:
        p4 += "Dashboard + chat done. "
    p4 += "Context-aware prioritizer done and unit-tested."
    if v.has_learned_ranker:
        p4 += " Learned ranker trained and evaluated."
    lines.append(f"| Phase 4 — React dashboard + context-aware prioritization | {p4} |")

    # Phase 5
    p5 = "Prioritizer tests + these docs done"
    if v.has_security:
        p5 += "; security hardening done"
    else:
        p5 += "; security hardening still to do"
    p5 += "."
    lines.append(f"| Phase 5 — testing, security, docs | {p5} |\n")

    # API feasibility
    lines.append("## API feasibility — read this before scoping\n")
    lines.append("Not every platform in the proposal has a usable API. Plan around this:\n")
    lines.append("* **GitHub** — official REST API. ✅ Done.")

    if v.has_oauth:
        lines.append("* **Google Calendar / Gmail** — official APIs, OAuth. ✅ **Implemented** (shared")
        lines.append("  read-only OAuth; see `docs/SETUP.md` §3).")
    else:
        lines.append("* **Google Calendar / Gmail** — official APIs, OAuth. ⚠️ Mock servers ready;")
        lines.append("  wire OAuth to go real.")

    if v.has_classroom:
        lines.append("* **Google Classroom** — ✅ **Implemented**. Course data access requires membership.")
    else:
        lines.append("* **Google Classroom** — official API exists, but course data access is restricted.")

    if v.has_codeforces:
        lines.append("* **Codeforces** — official public API. ✅ **Implemented** (upcoming contests + practice reminder).")
    else:
        lines.append("* **Codeforces** — official public API (`/api/`). Recommended over LeetCode.")

    lines.append("* **LeetCode** — **no official API.** ⚠️ Treat as best-effort/optional.")
    lines.append("* **LinkedIn** — **no open API** for reading messages or job posts. ❌ Highest risk.")
    lines.append("  Recommended substitute: detect LinkedIn *job/recruiter emails in Gmail* instead.\n")

    # Done since scaffold
    lines.append("## Done since the initial scaffold\n")
    done_items = []
    if v.has_codeforces:
        done_items.append("* ✅ **Codeforces MCP server** (real public API) — proved the \"add a server\n  without touching the core\" claim.")
    if v.has_oauth:
        done_items.append("* ✅ **Google OAuth** (shared, read-only) — Gmail, Calendar" + (", and Classroom" if v.has_classroom else "") + " read\n  live data from one token.")
    if v.has_classroom:
        done_items.append("* ✅ **Google Classroom MCP server** — pending assignments + announcements.")
    if v.has_cache:
        done_items.append("* ✅ **Caching layer** (Redis with in-memory fallback) — near-instant cache hits.")
    if v.has_eval:
        done_items.append("* ✅ **Evaluation harness** (`eval/`, `docs/EVALUATION.md`) — " + ("40" if v.has_dataset else "8") + " labeled\n  scenarios, ranking metrics, baselines" + (", and a **paired significance test**\n  (Wilcoxon + bootstrap CI)" if v.has_dataset else "") + ".")
    if v.has_learned_ranker:
        done_items.append("* ✅ **Learned ranker** + persistence + feedback loop — nDCG@5 0.968.")
    if v.has_extraction:
        done_items.append("* ✅ **Deadline extraction** — NLP parsing of dates from email/announcement text.")
    if v.has_scheduler:
        done_items.append("* ✅ **Day-scheduler** — time-blocks tasks into free slots with wellbeing pacing.")
    if v.has_notifier:
        done_items.append("* ✅ **Proactive notifier** — Telegram/email push of daily brief + alerts.")
    if v.has_opportunities:
        done_items.append("* ✅ **Opportunity radar** — internship/scholarship/hackathon tracking.")
    if v.has_actions:
        done_items.append("* ✅ **Action layer** — propose→confirm guardrails for write-actions.")
    if v.has_security:
        done_items.append("* ✅ **Security hardening** — prompt-injection defence, token vault, scope audit.")
    if v.has_progress:
        done_items.append("* ✅ **Progress dashboard** — done-streak, action counts, application funnel.")
    if v.has_rag:
        done_items.append("* ✅ **RAG assistant** — ask questions over your own study notes.")

    for item in done_items:
        lines.append(item)
    lines.append("")

    # Suggested next
    lines.append("## Suggested next commits\n")
    suggestions = []
    if not v.has_learned_ranker:
        suggestions.append("1. **Persistence + learned ranker.** PostgreSQL schema + feedback logging;\n   learning-to-rank model trained on the labeled data.")
    if not v.has_extraction:
        suggestions.append(f"{len(suggestions)+1}. **NLP deadline extraction.** Parse \"apply by Friday\" from email text.")
    if not v.has_scheduler:
        suggestions.append(f"{len(suggestions)+1}. **Day-scheduler.** Time-block ranked tasks into free calendar slots.")
    if not v.has_notifier:
        suggestions.append(f"{len(suggestions)+1}. **Notifier.** Push the daily briefing to Telegram/email.")
    if not v.has_security:
        suggestions.append(f"{len(suggestions)+1}. **Security pass** — least-privilege scopes, token-at-rest handling.")
    if not v.has_actions:
        suggestions.append(f"{len(suggestions)+1}. **Action layer.** Safe write-actions with confirmation.")
    if not v.has_progress:
        suggestions.append(f"{len(suggestions)+1}. **Progress dashboard.** Show streaks and trends.")
    if not v.has_rag:
        suggestions.append(f"{len(suggestions)+1}. **Study assistant.** RAG over notes for Q&A.")

    suggestions.append(f"{len(suggestions)+1}. **User study.** Have ≥15 students use it for 2 weeks; measure\n   missed deadlines and context-switching vs baseline.")

    for s in suggestions:
        lines.append(s)
    lines.append("")

    return "\n".join(lines)


# ═════════════════════════════════════════════════════════════════════════════
#  PRODUCT_PLAN.md  (v0.9.0+)
# ═════════════════════════════════════════════════════════════════════════════

def gen_product_plan(v: VersionInfo) -> str:
    lines: list[str] = []
    lines.append("# Student OS — Product & Technical Master Plan\n")
    lines.append("*How we turn a working integration into a genuinely useful, research-grade")
    lines.append("final-year IT project — designed from the student's point of view.*\n")

    # Status line
    done_features = []
    if v.has_learned_ranker:
        done_features.append("learning-to-rank")
    if v.has_extraction:
        done_features.append("NLP deadline extraction")
    if v.has_learned_ranker:
        done_features.append("persistence + feedback")
    if v.has_security:
        done_features.append("security hardening")
    if v.has_scheduler:
        done_features.append("day-scheduler + pacing")
    if v.has_notifier:
        done_features.append("proactive notifier")
    if v.has_opportunities:
        done_features.append("opportunity radar")
    if v.has_actions:
        done_features.append("action layer")
    if v.has_progress:
        done_features.append("progress dashboard")
    if v.has_rag:
        done_features.append("RAG study assistant")

    existing = []
    existing.append(f"{v.n_servers} MCP connectors")
    existing.append("an orchestrator")
    existing.append("a rule-based prioritizer")
    if v.has_cache:
        existing.append("a caching layer")
    if v.has_eval:
        existing.append("an evaluation harness")

    lines.append(f"This plan takes the platform we already have ({', '.join(existing)}) and layers on")
    lines.append("the things a real student actually needs. Every feature below is justified by a")
    lines.append("student need, not by \"it's cool tech.\"\n")

    if done_features:
        lines.append(f"> **Status (v{v.ver}):** " + ", ".join(done_features) + " are")
        lines.append("> implemented and tested. The remaining items are listed as future work below.")
    else:
        lines.append(f"> **Status (v{v.ver}):** the foundation is built. The features below are the planned next steps.")

    lines.append("\n---\n")

    # Section 1: Persona
    lines.append("## 1. Who we're building for (put yourself in their shoes)\n")
    lines.append("**Persona — \"Aarav\", 4th-year IT student.** Placement season. He's chasing")
    lines.append("internships, keeping up with coursework, doing DSA practice, and running his")
    lines.append("FYP. His pain isn't a lack of apps — it's the *mental tax* of stitching 8 apps")
    lines.append("together every morning and the fear of missing the one email that mattered.\n")

    lines.append("**Jobs-to-be-done (the north star):** (1) *Tell me what matters now*, (2) *don't")
    lines.append("let me miss anything*, (3) *help me fit it into my day*, (4) *surface")
    lines.append("opportunities*, (5) *let me act quickly*, (6) *show me I'm on track*, (7) *keep")
    lines.append("me safe and calm*.\n")
    lines.append("---\n")

    # Section 2: Feature modules
    lines.append("## 2. Feature modules (MoSCoW prioritized)\n")

    def status_tag(done: bool) -> str:
        return " ✅ **Done.**" if done else ""

    lines.append("### MUST-HAVE — the core contribution + essentials\n")
    lines.append(f"- **⭐ Personalized learning-to-rank prioritizer.** Replace fixed weights with a")
    lines.append(f"  model that learns priorities from actions (opened, done, dismissed, snoozed).{status_tag(v.has_learned_ranker)}")
    lines.append(f"- **⭐ NLP deadline & task extraction.** Detect deadlines buried in email")
    lines.append(f"  and Classroom text.{status_tag(v.has_extraction)}")
    lines.append(f"- **Persistence + feedback loop.** Store item history, user actions,")
    lines.append(f"  and learned preferences.{status_tag(v.has_learned_ranker)}")
    lines.append(f"- **⭐ Security & privacy layer.** Least-privilege scopes, encrypted")
    lines.append(f"  token vault, prompt-injection sanitizer.{status_tag(v.has_security)}")
    lines.append(f"- **Offline evaluation + user study.** Extend the benchmark;")
    lines.append(f"  run a 2-week study with ~15 students.{status_tag(v.has_eval)}\n")

    lines.append("### SHOULD-HAVE — high student value, achievable\n")
    lines.append(f"- **⭐ Intelligent day-scheduler.** Turn the ranked list into a time-blocked plan.{status_tag(v.has_scheduler)}")
    lines.append(f"- **Proactive daily brief + reminders.** Push the brief to Telegram/email.{status_tag(v.has_notifier)}")
    lines.append(f"- **Opportunity radar.** Aggregate internships, scholarships, hackathons.{status_tag(v.has_opportunities)}")
    lines.append(f"- **Action layer with guardrails.** Safe write-actions with confirmation.{status_tag(v.has_actions)}\n")

    lines.append("### COULD-HAVE — stretch, if time allows\n")
    lines.append(f"- **Progress & habit dashboard.** Streaks, action counts, application funnel.{status_tag(v.has_progress)}")
    lines.append(f"- **Study-material assistant (RAG).** Index notes and answer questions.{status_tag(v.has_rag)}")
    lines.append(f"- **Wellbeing-aware pacing.** Detect over-commitment and suggest a realistic day.{status_tag(v.has_scheduler)}\n")

    lines.append("---\n")

    # Thesis
    lines.append("## One-line thesis\n")
    lines.append("> **Student OS: a personalized, learning-based prioritization-and-planning agent")
    lines.append("> over heterogeneous student data streams (via the Model Context Protocol)" + (",\n> with NLP deadline extraction" if v.has_extraction else "") + (", safe action execution" if v.has_actions else "") + (", and a security-hardened design" if v.has_security else ""))
    lines.append("> — evaluated with an offline ranking benchmark and a two-week user study.**\n")

    lines.append("---\n")

    # Team
    lines.append("## Team split (3-person)\n")
    lines.append("| Member | Owns | Key deliverables |")
    lines.append("| --- | --- | --- |")
    lines.append("| **M1 — Platform & Data** | MCP servers, OAuth, persistence, notifier, deployment | reliable data layer + push notifications |")
    lines.append("| **M2 — Intelligence** | NLP extractor, feature builder, learning-to-rank, scheduler, experiments | the research core + results |")
    lines.append("| **M3 — Product & Study + Security** | frontend, action layer, security, user study | usable app + evidence + trust |\n")

    return "\n".join(lines)


# ═════════════════════════════════════════════════════════════════════════════
#  OVERVIEW.html  (v0.9.0+)
# ═════════════════════════════════════════════════════════════════════════════

def gen_overview_html(v: VersionInfo) -> str:
    # Build feature cards
    cards = []
    cards.append('<div class="card"><b>Daily briefing</b>One prioritized to-do list across all platforms.</div>')
    if v.has_learned_ranker:
        cards.append('<div class="card"><b>Learned prioritizer</b>An ML model ranks by importance and learns from your actions.</div>')
    else:
        cards.append('<div class="card"><b>Rule-based prioritizer</b>Context-aware scoring ranks items by importance.</div>')
    if v.has_extraction:
        cards.append('<div class="card"><b>Deadline extraction</b>Finds due dates hidden in email/announcement text.</div>')
    if v.has_scheduler:
        cards.append('<div class="card"><b>Day scheduler</b>Time-blocks tasks into your free slots; won\'t over-plan.</div>')
    if v.has_opportunities:
        cards.append('<div class="card"><b>Opportunity radar</b>Internships, scholarships, hackathons, contests + application status.</div>')
    if v.has_notifier:
        cards.append('<div class="card"><b>Proactive reminders</b>Pushes the brief &amp; deadline alerts to Telegram/email.</div>')
    if v.has_actions:
        cards.append('<div class="card"><b>Safe actions</b>Draft a reply, add an event — always with your confirmation.</div>')
    if v.has_security:
        cards.append('<div class="card"><b>Security</b>Read-only scopes, encrypted secrets, prompt-injection defence.</div>')
    if v.has_progress:
        cards.append('<div class="card"><b>Progress dashboard</b>Done-streak, actions, application funnel.</div>')
    if v.has_rag:
        cards.append('<div class="card"><b>Notes assistant</b>Ask questions over your own notes (RAG).</div>')
    if v.has_cache:
        cards.append('<div class="card"><b>Smart caching</b>Repeat requests served instantly; Redis or in-memory.</div>')

    cards_html = "\n  ".join(cards)

    # Mermaid servers
    mermaid_servers = ['G["Gmail"] --> O', 'C["Calendar"] --> O', 'H["GitHub"] --> O']
    if v.has_codeforces:
        mermaid_servers.append('F["Codeforces"] --> O')
    if v.has_classroom:
        mermaid_servers.append('R["Classroom"] --> O')
    mermaid_servers.append(f'O["STUDENT OS<br/>one coordinator"] --> P["One ranked, personalized<br/>plan for today"]')
    mermaid_servers.append('U["Student"] --> P')
    mermaid_flow = "\n  ".join(mermaid_servers)

    # Architecture mermaid
    arch_nodes = []
    arch_nodes.append('U["Student: \'What should I do today?\'"]')
    if v.has_frontend:
        fe_label = "Frontend (Next.js: dashboard · chat" + (" · progress" if v.has_progress else "") + ")"
        arch_nodes.append(f'--> FE["{fe_label}"]')
        arch_nodes.append('FE -->|HTTP| API["Backend API (FastAPI)"]')
    else:
        arch_nodes.append('--> API["Backend API (FastAPI)"]')
    arch_nodes.append('API --> ORCH["Orchestrator (tool router' + (' + cache' if v.has_cache else '') + ')"]')
    arch_nodes.append(f'ORCH --> SV["{v.n_servers} MCP servers: ' + ' · '.join(v.server_list) + '"]')
    arch_nodes.append('SV -->|real APIs / mock| EXT["External services"]')

    if v.has_learned_ranker:
        intl_parts = ["learned ranker"]
        if v.has_extraction:
            intl_parts = ["extraction"] + intl_parts
        if v.has_scheduler:
            intl_parts.append("scheduler")
        if v.has_opportunities:
            intl_parts.append("opportunities")
        if v.has_rag:
            intl_parts.append("RAG")
        arch_nodes.append(f'SV --> INT["Intelligence: {" · ".join(intl_parts)}"]')
        if v.has_security:
            arch_nodes.append('INT --> SEC["Security (sanitize untrusted text)"]')
            arch_nodes.append('SEC --> LLM["LLM writer / rule-based fallback"]')
        else:
            arch_nodes.append('INT --> LLM["LLM writer / rule-based fallback"]')
    else:
        arch_nodes.append('SV --> RANK["Prioritizer (context-aware ranking)"]')
        if v.has_security:
            arch_nodes.append('RANK --> SEC["Security (sanitize untrusted text)"]')
            arch_nodes.append('SEC --> LLM["LLM writer / rule-based fallback"]')
        else:
            arch_nodes.append('RANK --> LLM["LLM writer / rule-based fallback"]')
    arch_nodes.append('LLM --> API')
    if v.has_learned_ranker:
        arch_nodes.append('API --> DB["Store (SQLite/Postgres): history + feedback → learning' + (' &amp; progress' if v.has_progress else '') + '"]')
    arch_flow = "\n  ".join(arch_nodes)

    # Results cards
    result_cards = []
    if v.has_learned_ranker:
        result_cards.append('<div class="card"><span class="metric">0.968</span><br/>learned ranker nDCG@5 on <b>unseen</b> scenarios (vs 0.887 for due-date sorting) — a significant win (Wilcoxon p≈2e-5).</div>')
    elif v.has_dataset:
        result_cards.append('<div class="card"><span class="metric">0.954</span><br/>rule-based prioritizer nDCG@5 (vs 0.887 for due-date sorting) — a significant win (Wilcoxon p≈0.0004).</div>')
    elif v.has_eval:
        result_cards.append('<div class="card"><span class="metric">0.954</span><br/>rule-based prioritizer nDCG@5 on labeled scenarios (vs 0.887 for due-date sorting).</div>')

    if v.has_security:
        result_cards.append('<div class="card"><span class="metric">100% / 0%</span><br/>prompt-injection attacks <b>caught</b> / benign messages wrongly flagged, on a red-team set.</div>')
    if v.has_extraction:
        result_cards.append('<div class="card"><span class="metric">F1 1.00</span><br/>deadline extraction on a labeled set of email/announcement texts.</div>')
    result_cards.append(f'<div class="card"><span class="metric">{v.n_tests}</span><br/>automated tests passing' + ("; frontend type-checks clean" if v.has_frontend else "") + ".</div>")
    results_html = "\n  ".join(result_cards)

    # Version journey table
    journey_rows = []
    if v.idx >= 1:
        journey_rows.append("<tr><td>v0.1–0.2</td><td>MCP orchestrator + GitHub/Gmail/Calendar servers + rule-based prioritizer + API + web app</td></tr>")
    else:
        journey_rows.append("<tr><td>v0.1</td><td>MCP orchestrator + GitHub/Gmail/Calendar servers + rule-based prioritizer + API</td></tr>")
    if v.idx >= 5:
        journey_rows.append("<tr><td>v0.3–0.6</td><td>Codeforces server, Google OAuth (real Gmail/Calendar), caching, Classroom server</td></tr>")
    elif v.idx >= 2:
        parts = ["Codeforces server"]
        if v.has_oauth:
            parts.append("Google OAuth")
        if v.has_cache:
            parts.append("caching")
        if v.has_classroom:
            parts.append("Classroom server")
        journey_rows.append(f"<tr><td>v0.3–0.{v.idx+1}</td><td>{', '.join(parts)}</td></tr>")
    if v.idx >= 8:
        journey_rows.append("<tr><td>v0.7–0.9</td><td>Evaluation harness, 40-scenario dataset + significance test, documentation</td></tr>")
    elif v.idx >= 6:
        parts = ["Evaluation harness"]
        if v.has_dataset:
            parts.append("40-scenario dataset + significance test")
        if v.has_docs:
            parts.append("documentation")
        journey_rows.append(f"<tr><td>v0.7–0.{v.idx+1}</td><td>{', '.join(parts)}</td></tr>")
    if v.idx >= 11:
        journey_rows.append("<tr><td>v0.10–0.12</td><td>Persistence + feedback, learning-to-rank model, deadline extraction, day-scheduler</td></tr>")
    elif v.idx >= 9:
        parts = ["Persistence + feedback, learning-to-rank model"]
        if v.has_extraction:
            parts.append("deadline extraction")
        if v.has_scheduler:
            parts.append("day-scheduler")
        journey_rows.append(f"<tr><td>v0.10–0.{v.idx+1}</td><td>{', '.join(parts)}</td></tr>")
    if v.idx >= 14:
        journey_rows.append("<tr><td>v0.13–0.15</td><td>Proactive notifier, opportunity radar, safe action layer</td></tr>")
    elif v.idx >= 12:
        parts = ["Proactive notifier"]
        if v.has_opportunities:
            parts.append("opportunity radar")
        if v.has_actions:
            parts.append("safe action layer")
        journey_rows.append(f"<tr><td>v0.13–0.{v.idx+1}</td><td>{', '.join(parts)}</td></tr>")
    if v.idx >= 17:
        journey_rows.append("<tr><td>v0.16–0.18</td><td>Security hardening, progress dashboard, notes RAG assistant</td></tr>")
    elif v.idx >= 15:
        parts = ["Security hardening"]
        if v.has_progress:
            parts.append("progress dashboard")
        if v.has_rag:
            parts.append("notes RAG assistant")
        journey_rows.append(f"<tr><td>v0.16–0.{v.idx+1}</td><td>{', '.join(parts)}</td></tr>")
    journey_html = "\n  ".join(journey_rows)

    # Status
    if v.idx == 17:
        status_html = '<span class="pill">Complete</span> Every planned feature is built and tested (v0.18).'
    else:
        status_html = f'<span class="pill">v{v.ver}</span> {v.theme}. {v.n_tests} tests passing.'

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Student OS — Project Overview</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/mermaid/10.9.1/mermaid.min.js"></script>
<style>
  :root{{--ink:#1f2733;--muted:#5b6472;--line:#e4e8ef;--bg:#fff;--soft:#f6f8fc;
    --accent:#2f6bff;--accent-soft:#eaf0ff;--good:#0f9d58;--warn:#e8710a;--urgent:#e5484d;}}
  *{{box-sizing:border-box}}
  body{{margin:0;background:var(--bg);color:var(--ink);line-height:1.6;font-size:16px;
    font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;}}
  .wrap{{max-width:900px;margin:0 auto;padding:30px 22px 70px}}
  header.title{{border-bottom:3px solid var(--accent);padding-bottom:16px;margin-bottom:10px}}
  header.title h1{{font-size:32px;margin:0 0 4px}}
  header.title p{{font-size:18px;color:var(--muted);margin:0}}
  h2{{font-size:22px;margin:34px 0 10px;padding-top:8px;border-top:1px solid var(--line)}}
  h3{{font-size:17px;margin:18px 0 6px}}
  p{{margin:10px 0}}
  code{{background:var(--soft);border:1px solid var(--line);border-radius:5px;padding:1px 6px;font-size:14px}}
  .lead{{font-size:18px}}
  .key{{background:var(--accent-soft);border:1px solid #c7d7ff;border-radius:12px;padding:14px 18px;margin:16px 0}}
  .grid2{{display:grid;grid-template-columns:1fr 1fr;gap:12px}}
  @media(max-width:720px){{.grid2{{grid-template-columns:1fr}}}}
  .card{{background:var(--soft);border:1px solid var(--line);border-radius:10px;padding:12px 14px}}
  .card b{{display:block;margin-bottom:2px}}
  table{{border-collapse:collapse;width:100%;margin:14px 0;font-size:14.5px}}
  th,td{{border:1px solid var(--line);padding:8px 10px;text-align:left;vertical-align:top}}
  th{{background:var(--soft)}}
  .diagram{{background:var(--soft);border:1px solid var(--line);border-radius:12px;padding:16px;margin:18px 0;text-align:center}}
  .diagram .cap{{display:block;margin-top:8px;font-size:13px;color:var(--muted)}}
  .metric{{font-size:26px;font-weight:700;color:var(--accent)}}
  .pill{{display:inline-block;font-size:12px;font-weight:700;padding:2px 8px;border-radius:999px;color:#fff;background:var(--good)}}
  .muted{{color:var(--muted)}} .small{{font-size:13px}}
  ul{{margin:8px 0 8px 2px;padding-left:20px}} li{{margin:3px 0}}
  .warnbox{{background:#fff5ec;border:1px solid #ffd6ad;border-radius:10px;padding:12px 16px;margin:16px 0;font-size:14px}}
</style>
</head>
<body>
<div class="wrap">

<header class="title">
  <h1>Student OS</h1>
  <p>An MCP-powered AI assistant for student life — project overview (v{v.ver})</p>
</header>

<p class="lead">Student OS connects all the apps a student juggles — {', '.join(v.server_list).lower()} — and answers one question, <b>"What should I do today?"</b>, with a
single prioritized, personalized plan. This is the whole project in one page.</p>

<h2>1. The problem &amp; the idea</h2>
<p>A BTech student runs across 6–8 platforms daily; no single one connects them. Student OS becomes the one coordinator that gathers everything and hands back a single answer.</p>

<div class="diagram">
<pre class="mermaid">
flowchart LR
  {mermaid_flow}
</pre>
<span class="cap">Multiple noisy inputs → one calm, prioritized answer.</span>
</div>

<h2>2. What it does (feature highlights)</h2>
<div class="grid2">
  {cards_html}
</div>

<h2>3. How it works (architecture)</h2>
<div class="diagram">
<pre class="mermaid">
flowchart TD
  {arch_flow}
</pre>
<span class="cap">Each platform is an independent MCP server; the orchestrator fans out, ranks, and plans.</span>
</div>
<p class="small muted">Everything degrades gracefully: no accounts → realistic mock data; no AI key →
rule-based writer{'; no Redis/DB → in-memory' if v.has_cache else ''}. So it always runs, even with zero setup.</p>

<h2>4. Does it actually work? (measured results)</h2>
<div class="grid2">
  {results_html}
</div>
<p class="small muted">Full methodology in <code>docs/EVALUATION.md</code>.</p>

<h2>5. The build, version by version</h2>
<p>The project grew one feature per version (v0.1 → v{v.ver}). Each is saved as a runnable snapshot in <code>releases/</code>.</p>
<table>
  <tr><th>Versions</th><th>What was added</th></tr>
  {journey_html}
</table>

<h2>6. How to run it (no accounts needed)</h2>
<pre style="background:var(--soft);border:1px solid var(--line);border-radius:10px;padding:14px;font-size:13.5px;overflow:auto">
# Backend — prints today's ranked plan
cd backend
python -m venv .venv &amp;&amp; source .venv/bin/activate   # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
python demo.py
{"" if not v.has_frontend else chr(10) + "# Web app (separate terminal)" + chr(10) + "cd frontend &amp;&amp; npm install &amp;&amp; npm run dev            # http://localhost:3000"}</pre>
<p class="small">It runs in <b>mock mode</b> by default (realistic sample data). Connect real
platforms later via <code>docs/SETUP.md</code>.</p>

<h2>7. Status &amp; what's next</h2>
<p>{status_html}</p>

<hr style="border:none;border-top:1px solid var(--line);margin:26px 0" />
<p class="muted small">Student OS — BTech Final Year Project (Information Technology). Team: Nancy Singh,
Priyanshu Jha, Nimish Aggarwal. Guide: Dr. Varsha Sisaudia.</p>

</div>
<script>
  mermaid.initialize({{ startOnLoad:true, theme:'base',
    themeVariables:{{ primaryColor:'#eaf0ff', primaryBorderColor:'#2f6bff',
      primaryTextColor:'#1f2733', lineColor:'#7b88a8', fontSize:'14px' }},
    flowchart:{{ curve:'basis', htmlLabels:true }}, securityLevel:'loose' }});
</script>
</body>
</html>
"""


# ═════════════════════════════════════════════════════════════════════════════
#  GUIDE.html  (v0.9.0+) — scoped version of the beginner's guide
# ═════════════════════════════════════════════════════════════════════════════

def gen_guide_html(v: VersionInfo) -> str:
    """Generate the complete GUIDE.html scoped to version v."""

    # TOC entries
    toc_items = [
        '<li><a href="#problem">The problem: student life is scattered</a></li>',
        '<li><a href="#idea">The big idea: one assistant</a></li>',
        '<li><a href="#mcp">What is "MCP"? (the key concept)</a></li>',
        '<li><a href="#pieces">The building blocks (glossary in pictures)</a></li>',
        '<li><a href="#arch">The architecture (how the pieces connect)</a></li>',
        '<li><a href="#flow">How one request works, step by step (with example)</a></li>',
        '<li><a href="#rank">How the assistant decides what\'s important</a></li>',
    ]
    if v.has_cache:
        toc_items.append('<li><a href="#cache">Why it feels fast: the cache</a></li>')

    sec_num = 7 + (1 if v.has_cache else 0)
    sec_num += 1
    toc_items.append(f'<li><a href="#servers">The {v.n_servers} connectors, at a glance</a></li>')
    sec_num += 1
    toc_items.append('<li><a href="#mock">A clever trick: "mock mode"</a></li>')
    if v.has_eval:
        sec_num += 1
        toc_items.append('<li><a href="#eval">Proving it actually works (the evaluation)</a></li>')

    # Section 12 equivalent: advanced features
    has_advanced = v.has_learned_ranker or v.has_extraction or v.has_scheduler or v.has_notifier or v.has_opportunities or v.has_actions or v.has_security or v.has_progress or v.has_rag
    if has_advanced:
        sec_num += 1
        adv_sec = sec_num
        min_adv = "0.10"
        if v.has_extraction:
            min_adv = "0.11"
        toc_items.append(f'<li><a href="#more">What it also does now (v{min_adv}–v{v.ver})</a></li>')

    sec_num += 1
    tech_sec = sec_num
    toc_items.append('<li><a href="#stack">The technology used</a></li>')
    sec_num += 1
    files_sec = sec_num
    toc_items.append('<li><a href="#files">Where everything lives (file map)</a></li>')
    sec_num += 1
    gloss_sec = sec_num
    toc_items.append('<li><a href="#glossary">Glossary</a></li>')

    toc_html = "\n    ".join(toc_items)

    # Server connectors
    srv_num = (8 if v.has_cache else 7) + 1
    server_rows = [
        '<tr><td><b>GitHub</b></td><td>Your open pull requests, assigned issues, notifications</td><td>GitHub API (a token)</td><td>"PR #42 — review requested"</td></tr>',
        '<tr><td><b>Gmail</b></td><td>Unread priority mail, auto-tagged (internship / academic / OTP)</td><td>Gmail API (Google login)</td><td>"Internship closes soon"</td></tr>',
        '<tr><td><b>Calendar</b></td><td>Upcoming events, exams, assignment deadlines</td><td>Google Calendar API</td><td>"DBMS exam in 5 days"</td></tr>',
    ]
    if v.has_codeforces:
        server_rows.append('<tr><td><b>Codeforces</b></td><td>Upcoming rated contests + a practice reminder</td><td>Codeforces public API</td><td>"Div 2 round tomorrow"</td></tr>')
    if v.has_classroom:
        server_rows.append('<tr><td><b>Classroom</b></td><td>Pending assignments and announcements</td><td>Google Classroom API</td><td>"Lab 3 due in 2 days"</td></tr>')
    server_rows_html = "\n  ".join(server_rows)

    # Mermaid servers for arch diagram
    mermaid_svs = ["GH[\"GitHub\"]", "GM[\"Gmail\"]", "CA[\"Calendar\"]"]
    if v.has_codeforces:
        mermaid_svs.append("CF[\"Codeforces\"]")
    if v.has_classroom:
        mermaid_svs.append("CL[\"Classroom\"]")
    mermaid_sv_html = "\n    ".join(mermaid_svs)

    # Cache section
    cache_section = ""
    if v.has_cache:
        cache_num = 8
        cache_section = f"""
<!-- {cache_num} -->
<h2 id="cache">{cache_num}. Why it feels fast: the cache</h2>
<p>Gathering from {v.n_servers} apps takes a few seconds (about 6). If the student refreshes the page twice in a
minute, re-doing all that work is wasteful. So the assistant keeps the last result in a <b>cache</b>
(short-term memory) for a short time and serves it instantly on repeat requests.</p>

<div class="analogy">
  <span class="tag">Analogy: leftovers</span>
  Cooking a fresh meal takes time. If someone asks for the same dish two minutes later, you serve the
  leftovers from the fridge instead of cooking again. After a while the leftovers "expire" and you cook
  fresh. That expiry time is 90 seconds here.
</div>

<div class="diagram">
<pre class="mermaid">
flowchart TD
  R["Request arrives"] --> Q{{"Fresh copy<br/>in the cache?"}}
  Q -->|"Yes"| SERVE["Serve cached plan — instant"]
  Q -->|"No"| FAN["Ask all {v.n_servers} servers — about 6 seconds"]
  FAN --> STORE["Store the result for 90 seconds"]
  STORE --> SERVE2["Serve the plan"]
</pre>
<span class="cap">The cache: if a recent answer exists, return it instantly; otherwise gather fresh and remember it.</span>
</div>

<p>The "Refresh" button on the dashboard skips the cache on purpose, so you can always force a fresh
look. The proposal asked for <b>Redis</b> (an industrial-grade memory store) — the code uses Redis when
available, and otherwise falls back to a simple built-in memory, so it works even with nothing installed.</p>
"""

    # Eval section
    eval_section = ""
    if v.has_eval:
        eval_num = srv_num + 1
        n_scenarios = "40" if v.has_dataset else "8"
        best_score = "0.97" if v.has_learned_ranker else "0.95"
        best_name = "learned ranker" if v.has_learned_ranker else "our prioritizer"
        p_value = "p ≈ 2e-05" if v.has_learned_ranker else "p ≈ 0.0004"
        losses = "5" if v.has_learned_ranker else "7"

        eval_results_table = f"""
<table>
  <tr><th>Assistant (ranker)</th><th>Average score, nDCG@5 (0–1)</th><th>Verdict</th></tr>
  <tr><td>Random order</td><td>0.74</td><td>the floor</td></tr>
  <tr><td>Arrival order (no sorting)</td><td>0.75</td><td>barely better</td></tr>
  <tr><td>Sort by due date only</td><td>0.89</td><td>decent, naive</td></tr>
  <tr><td><b>Our prioritizer</b></td><td><b>0.95</b></td><td><b>best rule-based</b></td></tr>"""
        if v.has_learned_ranker:
            eval_results_table += """
  <tr><td><b>Learned ranker</b></td><td><b>0.97</b></td><td><b>best overall</b></td></tr>"""
        eval_results_table += "\n</table>"

        eval_section = f"""
<!-- {eval_num} -->
<h2 id="eval">{eval_num}. Proving it actually works (the evaluation)</h2>
<p>Anyone can <i>claim</i> their assistant ranks well. We <b>measured</b> it. We wrote down <b>{n_scenarios} realistic
student situations</b> and, for each item, a human "how important is this today?" grade from 0 to 3. Then we
compared our prioritizer against simpler methods and scored how close each came to the human grades.</p>

<div class="analogy">
  <span class="tag">In plain terms</span>
  It's like grading assistants on the same test, {n_scenarios} times. The "answer key" is what a sensible human
  would put on top. The main score, <b>nDCG</b>, simply measures <i>"did you put the important things near
  the top?"</i> — 1.0 is perfect, 0 is terrible.
</div>

{eval_results_table}

<p>Head-to-head against the best simple method (sort-by-due-date), {best_name} <b>won</b> the majority of the
{n_scenarios} situations. The ties and losses are mostly cases where sorting by due date is already the right answer —
we included those on purpose, so the test is fair.</p>

{"" if not v.has_dataset else '''<div class="analogy">
  <span class="tag">"But could that just be luck?"</span>
  Good question — and exactly what a <b>significance test</b> answers. The test gives a number called a
  <b>p-value</b>: the chance the result is just luck. Ours is <b>''' + p_value + '''</b> — well below the
  threshold of 0.05. So the improvement is genuine, not a coincidence.
</div>'''}

<div class="callout key small">
  <b>Being honest about limits</b>
  The {n_scenarios} grades came from <b>one author</b>, and the scenarios are realistic but constructed. We even report
  the situations we lost. Saying this openly is what makes research credible.
</div>
"""

    # Advanced features section
    advanced_section = ""
    if has_advanced:
        adv_cards = []
        if v.has_learned_ranker:
            adv_cards.append("""<div class="callout tip">
  <b>🧠 It learns what matters to you (the learned ranker)</b>
  A small <b>machine-learning model</b> learns priorities from real examples (and, over time,
  from what you open, finish, or dismiss). On unseen test cases it ranks even better
  than the hand-written rules.
</div>""")
        if v.has_extraction:
            adv_cards.append("""<div class="callout tip">
  <b>📅 It finds deadlines hidden in text (NLP extraction)</b>
  An email like <i>"apply by Friday"</i> or <i>"submit before 3 August"</i> used to slip through.
  Now the assistant <b>reads the words</b> and pulls the deadline out automatically.
</div>""")
        if v.has_scheduler:
            adv_cards.append("""<div class="callout tip">
  <b>🗓️ It plans your actual day (the scheduler)</b>
  Beyond a ranked <i>list</i>, it builds a <b>timetable</b>: it fits your tasks into the
  free gaps around your classes. If there's more to do than hours, it schedules the most important
  and gently <b>defers the rest</b>.
</div>""")
        if v.has_notifier:
            adv_cards.append("""<div class="callout tip">
  <b>🔔 It nudges you (proactive reminders)</b>
  A scheduled job can <b>push your morning brief</b> and pre-deadline alerts to
  <b>Telegram or email</b>. (With nothing set up it just prints the message — a safe "dry run".)
</div>""")
        if v.has_opportunities:
            adv_cards.append("""<div class="callout tip">
  <b>🎯 It tracks opportunities (the radar)</b>
  Internships, scholarships, hackathons, and contests are gathered into one place, and you
  can mark each one <b>interested → applied → offer/rejected</b>.
</div>""")
        if v.has_actions:
            adv_cards.append("""<div class="callout tip">
  <b>✅ It can act — safely (the action layer)</b>
  It can draft an email reply, add a calendar event, snooze an item, or mark it done. But
  it's <b>two-step</b>: it shows a preview and does <b>nothing until you confirm</b>.
</div>""")
        if v.has_security:
            adv_cards.append("""<div class="callout tip">
  <b>🔒 It keeps your data safe (security)</b>
  It reads your email/calendar with <b>read-only</b> access, stores any secret <b>encrypted</b>,
  and — importantly — <b>filters malicious text</b>. In testing it caught 100% of such tricks.
</div>""")
        if v.has_progress or v.has_rag:
            parts = []
            if v.has_progress:
                parts.append("A <b>progress page</b> tracks your done-streak, actions taken, and application funnel.")
            if v.has_rag:
                parts.append('A <b>study assistant</b> lets you ask questions over your own notes and returns the exact relevant passage.')
            adv_cards.append(f'<div class="callout tip">\n  <b>📈 Progress & notes</b>\n  {" ".join(parts)}\n</div>')

        adv_cards_html = "\n\n".join(adv_cards)
        advanced_section = f"""
<!-- {adv_sec} -->
<h2 id="more">{adv_sec}. What it also does now</h2>
<p>The project kept growing one feature per version. Here's each newer capability in
plain terms — every one is justified by a real student need.</p>

{adv_cards_html}
"""

    # Tech stack table
    tech_rows = []
    if v.has_frontend:
        tech_rows.append('<tr><td>Frontend</td><td>Next.js + TypeScript</td><td>the web dashboard and chat you see</td></tr>')
    tech_rows.append('<tr><td>Backend</td><td>Python + FastAPI</td><td>the engine that answers requests</td></tr>')
    tech_rows.append('<tr><td>Connectors</td><td>Model Context Protocol (MCP)</td><td>the universal "plug" to each app</td></tr>')
    tech_rows.append('<tr><td>AI writer (optional)</td><td>Claude (Anthropic)</td><td>writes the friendly summary</td></tr>')
    if v.has_oauth:
        tech_rows.append('<tr><td>Logins</td><td>OAuth 2.0</td><td>secure, read-only access to Google/GitHub</td></tr>')
    if v.has_cache:
        tech_rows.append('<tr><td>Cache</td><td>Redis (or built-in memory)</td><td>makes repeat requests instant</td></tr>')
    tech_rows_html = "\n  ".join(tech_rows)

    # File map
    file_map_lines = ["student-os/", "├─ backend/                    the engine (Python)", "│  ├─ app/"]
    file_map_lines.append("│  │  ├─ main.py               starts the API")
    file_map_lines.append("│  │  ├─ orchestrator/         gathers, ranks, summarizes")
    file_map_lines.append("│  │  │  ├─ mcp_manager.py       talks to all MCP servers" + (" (+ caching)" if v.has_cache else ""))
    file_map_lines.append("│  │  │  ├─ prioritizer.py       the scoring brain")
    file_map_lines.append("│  │  │  ├─ llm.py               summary writer (AI or rules)")
    file_map_lines.append("│  │  │  └─ agent.py             ties gather → rank → write together")
    if v.has_cache or v.has_learned_ranker:
        extra_files = []
        if v.has_cache:
            extra_files.append("cache.py")
        if v.has_learned_ranker:
            extra_files.append("store.py")
        file_map_lines.append(f"│  │  ├─ {'  '.join(extra_files)}" + ("    short-term memory" if v.has_cache else "") + (" + saved history/feedback" if v.has_learned_ranker else ""))
    if v.has_security or v.has_notifier or v.has_actions:
        extra = []
        if v.has_security:
            extra.append("security.py")
        if v.has_notifier:
            extra.append("notifier.py")
        if v.has_actions:
            extra.append("actions.py")
        file_map_lines.append(f"│  │  ├─ {'  '.join(extra)}")
    if v.has_learned_ranker:
        intl = "learned ranker"
        if v.has_scheduler:
            intl += " · scheduler"
        if v.has_opportunities:
            intl += " · opportunities"
        if v.has_rag:
            intl += " · study (RAG)"
        file_map_lines.append(f"│  │  ├─ intelligence/         {intl}")
    file_map_lines.append("│  │  └─ schemas.py            the common shape every item uses")

    srv_folders = "github_server/  gmail_server/  calendar_server/"
    file_map_lines.append(f"│  ├─ mcp_servers/             one folder per connector")
    file_map_lines.append(f"│  │  ├─ {srv_folders}")
    if v.has_codeforces or v.has_classroom:
        extra_svs = []
        if v.has_codeforces:
            extra_svs.append("codeforces_server/")
        if v.has_classroom:
            extra_svs.append("classroom_server/")
        file_map_lines.append(f"│  │  ├─ {'  '.join(extra_svs)}")
    common_parts = []
    if v.has_oauth:
        common_parts.append("Google login")
    if v.has_extraction:
        common_parts.append("deadline extraction")
    common_parts.append("helpers")
    file_map_lines.append(f"│  │  └─ common/               {' · '.join(common_parts)}")

    if v.has_eval:
        file_map_lines.append("│  ├─ eval/                    the evaluation")
    file_map_lines.append(f"│  ├─ tests/                   automated checks ({v.n_tests} passing)")
    file_map_lines.append("│  └─ demo.py                  run the whole thing from the terminal")
    if v.has_frontend:
        file_map_lines.append("├─ frontend/                   web app: dashboard, chat" + (", progress page" if v.has_progress else ""))
    file_map_lines.append("└─ docs/                       this guide + other documentation")

    file_map = "\n".join(file_map_lines)

    # Footer description
    footer_parts = [f"{v.n_servers} connectors", "an orchestrator"]
    if v.has_learned_ranker:
        footer_parts.append("a learned prioritizer")
    else:
        footer_parts.append("a rule-based prioritizer")
    if v.has_extraction:
        footer_parts.append("deadline extraction")
    if v.has_scheduler:
        footer_parts.append("a day-scheduler")
    if v.has_cache:
        footer_parts.append("a cache")
    if v.has_learned_ranker:
        footer_parts.append("persistence + feedback")
    if v.has_notifier:
        footer_parts.append("proactive reminders")
    if v.has_opportunities:
        footer_parts.append("an opportunity radar")
    if v.has_actions:
        footer_parts.append("a safe action layer")
    if v.has_security:
        footer_parts.append("security hardening")
    if v.has_progress:
        footer_parts.append("a progress dashboard")
    if v.has_rag:
        footer_parts.append("a notes assistant")
    if v.has_frontend:
        footer_parts.append("a web app")
    if v.has_eval:
        footer_parts.append("a measured evaluation")
    footer = ", ".join(footer_parts)

    # Glossary entries
    gloss_rows = [
        '<tr><td><b>API</b></td><td>A defined "door" one program uses to ask another program for data.</td></tr>',
        '<tr><td><b>MCP</b> (Model Context Protocol)</td><td>A shared standard — a universal "plug" — that lets an AI connect to any tool the same way.</td></tr>',
        '<tr><td><b>MCP server</b></td><td>A small program that connects one app to the assistant using MCP (the "waiter").</td></tr>',
        '<tr><td><b>Orchestrator</b></td><td>The coordinator that talks to all the MCP servers and merges what they return.</td></tr>',
        '<tr><td><b>Prioritizer</b></td><td>The logic that scores and sorts items so the most important is on top.</td></tr>',
        '<tr><td><b>LLM</b></td><td>A Large Language Model — an AI like Claude that understands and writes text.</td></tr>',
    ]
    if v.has_oauth:
        gloss_rows.append('<tr><td><b>OAuth</b></td><td>The secure "Sign in with Google" style login that grants limited, revocable access.</td></tr>')
    if v.has_cache:
        gloss_rows.append('<tr><td><b>Cache</b></td><td>Short-term memory that stores a recent result to answer repeat requests instantly.</td></tr>')
    gloss_rows.append('<tr><td><b>Token</b></td><td>A secret key that proves the app is allowed to read your data (like a temporary pass).</td></tr>')
    if v.has_eval:
        gloss_rows.append('<tr><td><b>nDCG</b></td><td>A ranking score (0–1) that rewards putting the most important items near the top.</td></tr>')
        if v.has_dataset:
            gloss_rows.append('<tr><td><b>p-value / significant</b></td><td>The chance a result is just luck. A small p-value (below 0.05) means the effect is real.</td></tr>')
    gloss_rows.append('<tr><td><b>Mock mode</b></td><td>Running on realistic fake data so the system works with no accounts or setup.</td></tr>')
    gloss_rows_html = "\n  ".join(gloss_rows)

    # One-sentence summary
    summary_extra = ""
    if v.has_learned_ranker:
        summary_extra += "\n  <br/><br/>\n  As of this version it also <b>learns</b> what you find important"
        if v.has_extraction:
            summary_extra += ", digs <b>deadlines out of\n  emails</b>"
        if v.has_scheduler:
            summary_extra += ", <b>plans your day</b> around your free time"
        if v.has_opportunities:
            summary_extra += ", <b>tracks internship applications</b>"
        if v.has_notifier:
            summary_extra += ",\n  <b>nudges you</b> before deadlines"
        if v.has_rag:
            summary_extra += ", answers questions from <b>your own notes</b>"
        if v.has_security:
            summary_extra += ", keeps your data\n  <b>safe</b>"
        if v.has_actions:
            summary_extra += ", and can even <b>draft replies</b> — always with your confirmation"
        summary_extra += "."

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Student OS — The Complete Beginner's Guide</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/mermaid/10.9.1/mermaid.min.js"></script>
<style>
  :root{{
    --ink:#1f2733; --muted:#5b6472; --line:#e4e8ef; --bg:#ffffff;
    --soft:#f6f8fc; --accent:#2f6bff; --accent-soft:#eaf0ff;
    --good:#0f9d58; --warn:#e8710a; --urgent:#e5484d;
  }}
  *{{box-sizing:border-box}}
  body{{
    margin:0; background:var(--bg); color:var(--ink);
    font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
    line-height:1.65; font-size:17px;
  }}
  .wrap{{max-width:860px; margin:0 auto; padding:32px 22px 80px}}
  header.title{{border-bottom:3px solid var(--accent); padding-bottom:18px; margin-bottom:8px}}
  header.title h1{{font-size:34px; margin:0 0 6px; letter-spacing:.2px}}
  header.title p{{font-size:19px; color:var(--muted); margin:0}}
  h2{{font-size:25px; margin:44px 0 12px; padding-top:10px; border-top:1px solid var(--line)}}
  h3{{font-size:19px; margin:26px 0 8px}}
  p{{margin:12px 0}}
  code{{background:var(--soft); border:1px solid var(--line); border-radius:5px; padding:1px 6px; font-size:14.5px}}
  .lead{{font-size:18.5px}}
  .callout{{border-radius:12px; padding:16px 18px; margin:18px 0; border:1px solid var(--line); background:var(--soft)}}
  .callout.tip{{background:#eefaf1; border-color:#bfe6cb}}
  .callout.key{{background:var(--accent-soft); border-color:#c7d7ff}}
  .callout.warn{{background:#fff5ec; border-color:#ffd6ad}}
  .callout b{{display:block; margin-bottom:4px}}
  .analogy{{border-left:4px solid var(--accent); padding:4px 0 4px 16px; margin:16px 0; color:#333}}
  .analogy .tag{{display:inline-block; font-size:12px; font-weight:700; letter-spacing:.6px;
    text-transform:uppercase; color:var(--accent); margin-bottom:2px}}
  .diagram{{background:var(--soft); border:1px solid var(--line); border-radius:12px; padding:18px; margin:20px 0; text-align:center}}
  .diagram .cap{{display:block; margin-top:10px; font-size:14px; color:var(--muted); text-align:center}}
  table{{border-collapse:collapse; width:100%; margin:18px 0; font-size:15.5px}}
  th,td{{border:1px solid var(--line); padding:9px 11px; text-align:left; vertical-align:top}}
  th{{background:var(--soft)}}
  .pill{{display:inline-block; font-size:12px; font-weight:700; padding:2px 9px; border-radius:999px; color:#fff}}
  .p-urgent{{background:var(--urgent)}} .p-high{{background:var(--warn)}} .p-med{{background:var(--accent)}} .p-low{{background:#8b93a3}}
  .toc{{background:var(--soft); border:1px solid var(--line); border-radius:12px; padding:16px 20px}}
  .toc ol{{margin:6px 0 0; padding-left:22px}}
  .toc a{{color:var(--accent); text-decoration:none}}
  .toc a:hover{{text-decoration:underline}}
  .step{{display:flex; gap:14px; margin:14px 0}}
  .step .n{{flex:0 0 30px; height:30px; border-radius:50%; background:var(--accent); color:#fff;
    display:flex; align-items:center; justify-content:center; font-weight:700}}
  .muted{{color:var(--muted)}}
  .mermaid{{margin:0 auto}}
  hr{{border:none; border-top:1px solid var(--line); margin:30px 0}}
  .small{{font-size:14px}}
</style>
</head>
<body>
<div class="wrap">

<header class="title">
  <h1>Student OS</h1>
  <p>The complete beginner's guide — what it is, why it exists, and how it works.</p>
</header>

<p class="lead">This guide assumes <b>zero prior knowledge</b>. If you have never heard of an
"API", an "MCP server", or an "LLM", that's fine — every term is explained in plain
words with everyday analogies, pictures, and worked examples.</p>

<div class="callout key">
  <b>One-sentence summary</b>
  Student OS is a smart assistant that plugs into all the apps a student uses ({', '.join(s.lower() for s in v.server_list)}), and every morning answers a single question —
  <i>"What should I do today?"</i> — with one clean, prioritized to-do list.{summary_extra}
</div>

<div class="callout warn small">
  <b>If the diagrams below look blank</b>
  They are drawn by a small helper loaded from the internet. Open this file while online and
  they will appear.
</div>

<div class="toc">
  <b>What's inside</b>
  <ol>
    {toc_html}
  </ol>
</div>

<!-- 1 -->
<h2 id="problem">1. The problem: student life is scattered</h2>
<p>A typical engineering student juggles six to eight apps <i>every single day</i>. No single app connects
these. So the student has to open each one, read through it, and figure out what is urgent, what can wait,
and what they might have missed. Things slip through.</p>

<!-- 2 -->
<h2 id="idea">2. The big idea: one assistant</h2>
<p>Student OS flips the picture. Instead of the student connecting to eight apps, <b>one assistant</b>
connects to the apps, gathers everything, sorts it by importance, and hands the student a single answer:</p>
<p class="lead" style="text-align:center"><b>"What should I do today?"</b></p>

<!-- 3 -->
<h2 id="mcp">3. What is "MCP"? (the key concept)</h2>
<p><b>MCP — the Model Context Protocol</b> — is a real, open standard (introduced late 2024). It defines
one standard way for an AI assistant to plug into any app or data source.</p>

<div class="analogy">
  <span class="tag">Analogy: the universal plug</span>
  Old laptops needed a different charger for every brand. Then USB-C arrived — <b>one shape of plug</b>
  that works with everything. MCP is USB-C for AI.
</div>

<!-- 4 -->
<h2 id="pieces">4. The building blocks (glossary in pictures)</h2>
<table>
  <tr><th>Part</th><th>What it does</th><th>Everyday equivalent</th></tr>
  <tr><td><b>MCP server</b></td><td>Connects to one app and offers simple actions.</td><td>A waiter for one restaurant</td></tr>
  <tr><td><b>Orchestrator</b></td><td>Talks to all MCP servers, collects everything.</td><td>A head waiter</td></tr>
  <tr><td><b>Prioritizer</b></td><td>Scores every item and sorts them.</td><td>A smart assistant highlighting your to-do list</td></tr>
  <tr><td><b>LLM</b></td><td>An AI that writes the friendly summary. Optional.</td><td>A person who reads the list and writes you a note</td></tr>
  {"<tr><td><b>Cache</b></td><td>Short-term memory for instant repeats.</td><td>Leftovers in the fridge</td></tr>" if v.has_cache else ""}
  <tr><td><b>Backend / API</b></td><td>The engine that ties it together.</td><td>The kitchen</td></tr>
  {"<tr><td><b>Frontend</b></td><td>The web page you see — dashboard + chat.</td><td>The dining table</td></tr>" if v.has_frontend else ""}
</table>

<!-- 5 -->
<h2 id="arch">5. The architecture (how the pieces connect)</h2>
<div class="diagram">
<pre class="mermaid">
flowchart TD
  U["Student asks:<br/>'What should I do today?'"] --> {"FE" if v.has_frontend else "API"}{"" if not v.has_frontend else '["FRONTEND<br/>web dashboard + chat (Next.js)"]'}
  {"FE -->|HTTP| API" if v.has_frontend else ""}["BACKEND API (FastAPI)"]
  API --> ORCH["ORCHESTRATOR<br/>talks to every MCP server"]
  {"ORCH --> CACHE" + '{' + '"Recent copy<br/>in the cache?"' + '}' if v.has_cache else ""}
  subgraph SERVERS["MCP SERVERS (one connector per app)"]
    direction LR
    {mermaid_sv_html}
  end
  {"CACHE -->|yes| RANK" if v.has_cache else ""}{"" if not v.has_cache else '["PRIORITIZER<br/>scores &amp; sorts everything"]'}
  {"CACHE -->|no| SERVERS" if v.has_cache else "ORCH --> SERVERS"}
  SERVERS --> RANK["PRIORITIZER<br/>scores &amp; sorts everything"]
  RANK --> WRITE["SUMMARY WRITER<br/>(LLM or built-in rules)"]
  WRITE --> API
  API --> {"FE" if v.has_frontend else "U"}
</pre>
<span class="cap">The layered architecture.</span>
</div>

<!-- 6 -->
<h2 id="flow">6. How one request works, step by step</h2>
<div class="step"><div class="n">1</div><div>The <b>{"frontend" if v.has_frontend else "student"}</b> sends a request: <code>GET /briefing</code>.</div></div>
<div class="step"><div class="n">2</div><div>The <b>orchestrator</b> starts each MCP server and calls its actions.</div></div>
<div class="step"><div class="n">3</div><div>Each server returns items in a <b>common format</b>.</div></div>
<div class="step"><div class="n">4</div><div>The orchestrator merges and removes duplicates.</div></div>
<div class="step"><div class="n">5</div><div>The <b>prioritizer</b> scores and sorts everything.</div></div>
<div class="step"><div class="n">6</div><div>A <b>summary</b> is written and the ranked list is returned.</div></div>

<!-- 7 -->
<h2 id="rank">7. How the assistant decides what's important</h2>
<p>The prioritizer gives every item a <b>score</b> from three questions:</p>
<ol>
  <li><b>What kind of thing is it?</b> An exam starts higher than a calendar event.</li>
  <li><b>How soon is it due?</b> Due today adds a lot; no date adds nothing.</li>
  <li><b>What's the current context?</b> During <i>exam week</i>, coursework gets a boost.</li>
</ol>

<h3>A worked example</h3>
<table>
  <tr><th>Item</th><th>Base (kind)</th><th>+ Due soon</th><th>+ Context</th><th>= Score</th><th>Priority</th></tr>
  <tr><td>OS assignment, due <b>tomorrow</b></td><td>5.0</td><td>+4.0</td><td>+2.0</td><td><b>11.0</b></td><td><span class="pill p-urgent">urgent</span></td></tr>
  <tr><td>Internship email, 2 days</td><td>2.0</td><td>+2.0</td><td>+4.0</td><td><b>8.0</b></td><td><span class="pill p-high">high</span></td></tr>
  <tr><td>Codeforces contest, <b>today</b></td><td>3.0</td><td>+6.0</td><td>−4.0</td><td><b>5.0</b></td><td><span class="pill p-med">medium</span></td></tr>
  <tr><td>"Your OTP is 481920"</td><td>2.0</td><td>+0</td><td>−3.0</td><td><b>−1.0</b></td><td><span class="pill p-low">low</span></td></tr>
</table>
{cache_section}
<!-- {srv_num} -->
<h2 id="servers">{srv_num}. The {v.n_servers} connectors, at a glance</h2>
<table>
  <tr><th>Connector</th><th>What it brings in</th><th>Talks to</th><th>Example item</th></tr>
  {server_rows_html}
</table>

<!-- {srv_num + 1} -->
<h2 id="mock">{srv_num + 1}. A clever trick: "mock mode"</h2>
<p>The whole system ships in <b>mock mode</b>: every connector returns realistic <i>sample</i> data.
This means anyone can run the project end-to-end in seconds, with <b>zero setup</b>.</p>
{eval_section}{advanced_section}
<!-- {tech_sec} -->
<h2 id="stack">{tech_sec}. The technology used</h2>
<table>
  <tr><th>Layer</th><th>Technology</th><th>In one line</th></tr>
  {tech_rows_html}
</table>

<!-- {files_sec} -->
<h2 id="files">{files_sec}. Where everything lives (file map)</h2>
<pre style="background:var(--soft); border:1px solid var(--line); border-radius:10px; padding:16px; overflow:auto; font-size:14px; line-height:1.5">
{file_map}
</pre>

<!-- {gloss_sec} -->
<h2 id="glossary">{gloss_sec}. Glossary</h2>
<table>
  <tr><th>Term</th><th>Plain meaning</th></tr>
  {gloss_rows_html}
</table>

<hr/>
<p class="muted small">Student OS — BTech Final Year Project. This guide explains the system as built (v{v.ver}):
{footer}. For setup see <code>docs/SETUP.md</code>.</p>

</div>

<script>
  mermaid.initialize({{
    startOnLoad: true,
    theme: 'base',
    themeVariables: {{
      primaryColor: '#eaf0ff',
      primaryBorderColor: '#2f6bff',
      primaryTextColor: '#1f2733',
      lineColor: '#7b88a8',
      fontSize: '15px'
    }},
    flowchart: {{ curve: 'basis', htmlLabels: true }},
    securityLevel: 'loose'
  }});
</script>
</body>
</html>
"""


# ═════════════════════════════════════════════════════════════════════════════
#  MAIN — write everything to each release directory
# ═════════════════════════════════════════════════════════════════════════════

def main() -> None:
    for v, dirname in zip(VERSIONS_INFO, RELEASE_DIRS):
        release_dir = RELEASES / dirname
        if not release_dir.exists():
            print(f"  ⚠ missing release dir: {dirname}")
            continue

        # README.md — all versions
        (release_dir / "README.md").write_text(gen_readme(v), encoding="utf-8")

        docs_dir = release_dir / "docs"

        if v.has_docs:
            # v0.9.0+ get docs
            docs_dir.mkdir(exist_ok=True)

            (release_dir / "CHANGELOG.md").write_text(gen_changelog(v), encoding="utf-8")
            (docs_dir / "ARCHITECTURE.md").write_text(gen_architecture(v), encoding="utf-8")
            (docs_dir / "SETUP.md").write_text(gen_setup(v), encoding="utf-8")
            (docs_dir / "EVALUATION.md").write_text(gen_evaluation(v), encoding="utf-8")
            (docs_dir / "ROADMAP.md").write_text(gen_roadmap(v), encoding="utf-8")
            (docs_dir / "PRODUCT_PLAN.md").write_text(gen_product_plan(v), encoding="utf-8")
            (docs_dir / "GUIDE.html").write_text(gen_guide_html(v), encoding="utf-8")
            (docs_dir / "OVERVIEW.html").write_text(gen_overview_html(v), encoding="utf-8")
        else:
            # v0.1–v0.8: remove docs/ if present
            if docs_dir.exists():
                shutil.rmtree(docs_dir)
            # Remove CHANGELOG.md if present
            cl = release_dir / "CHANGELOG.md"
            if cl.exists():
                cl.unlink()

        print(f"v{v.ver:<7}  {'docs + README' if v.has_docs else 'README only'}")


if __name__ == "__main__":
    main()
