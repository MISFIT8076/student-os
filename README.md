# Kairo (καιρός)

**An MCP-powered, learning-based AI coordination layer for student life & academic focus.**  
BTech Final Year Project — CSE/IT. Current version: **v0.18.0**.

> *“In ancient Greek philosophy, **Chronos** (χρόνος) is quantitative, sequential clock time. **Kairos** (καιρός) is the qualitative, supreme, opportune moment — the right time to act.”*

Instead of checking eight apps every morning, a student asks one question — *"What should I do today?"* — and **Kairo** reads across their connected platforms (GitHub, Gmail, Google Calendar, Codeforces, Google Classroom), **ranks** every signal using a trained learning-to-rank model, **extracts** deadlines hidden in prose, **synthesizes** an opportune day plan with wellbeing pacing, **tracks** career opportunities, and can safely **act** — all from one classical, responsive interface.

Built natively on the **Model Context Protocol (MCP)**: each platform operates as an isolated MCP server exposing standardized tools. An intelligent orchestrator coordinates tool discovery, normalization, deduplication, and ranking.

---

## ✨ Features & Highlights

- **🏛️ Classical Greek Aesthetic & Theme Switcher:**
  - **Aegean Dark (Default):** Deep obsidian night (`#070b14`), Corinthian gold (`#f59e0b`), celestial azure (`#38bdf8`), and Spartan crimson.
  - **Parian Light:** Polished marble alabaster (`#f8fafc`), warm bronze accents (`#b45309`), and crisp elevated cards.
  - Smooth transitions with instant anti-FOUC persistence in `localStorage`.
- **✦ Ranked Focus Horizon:** Context-aware learned ranking of cross-platform action items with real-time filtering, source badges, and deadline indicators.
- **◷ Kairos Day Scheduler:** Automated time-blocking with wellbeing pacing advice and deferred overflow management to prevent academic burnout.
- **◎ Opportunity Radar:** Active tracking and application status management for internships, hackathons, contests, and scholarships.
- **🏛️ Oracle of Kairo:** Autonomous, tool-augmented conversational assistant ready to answer questions and plan deep-work blocks.
- **🛡️ Built-in Security Layer:** Strict indirect prompt-injection sanitization, Fernet token vault encryption, and read-only scope auditing.
- **📈 Progress & Habit Funnel:** Longitudinal streak tracking and action distribution over time (`/progress`).

---

## ⚡ Runs Immediately — No Accounts or Keys Needed

The whole system ships with **mock mode enabled by default** (`STUDENT_OS_MOCK=true`):
every server returns realistic sample data, so you can test and explore the full MCP pipeline before configuring any external API keys (see `docs/SETUP.md` for live Google/GitHub integration).

## Quickstart

```bash
# 1. Backend (FastAPI API)
cd backend
python -m venv .venv && source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python demo.py                    # prints today's ranked plan in CLI
uvicorn app.main:app --reload     # runs API at http://127.0.0.1:8000 (Docs: /docs)

# 2. Frontend (Next.js Dashboard)
cd frontend
npm install
npm run dev                       # runs web dashboard at http://localhost:3000
```

Optional: `python -m app.intelligence.train` trains the learning-to-rank model, then set `RANKER=learned`. Full credentials setup for Google/GitHub is documented in `docs/SETUP.md`.

---

## Capability Map

| Capability | Module | Introduced |
| --- | --- | --- |
| MCP orchestrator (tool router, dedupe, cache) | `app/orchestrator/mcp_manager.py` | v0.1 |
| 5 MCP servers: GitHub, Gmail, Calendar, Codeforces, Classroom | `mcp_servers/` | v0.1–0.6 |
| Context-aware **rule-based** prioritizer (baseline) | `app/orchestrator/prioritizer.py` | v0.1 |
| **Learning-to-rank** prioritizer (trained, pluggable) | `app/intelligence/` | v0.10 |
| Caching (Redis or in-memory) | `app/cache.py` | v0.5 |
| Persistence + feedback loop (SQLite/Postgres) | `app/store.py` | v0.10 |
| **NLP deadline extraction** from unstructured text | `mcp_servers/common/extraction.py` | v0.11 |
| **Day-scheduler** + wellbeing pacing | `app/intelligence/scheduler.py` | v0.12 |
| **Proactive notifier** (Telegram/email/dry-run) | `app/notifier.py` | v0.13 |
| **Opportunity radar** + application tracking | `app/intelligence/opportunities.py` | v0.14 |
| **Action layer** (propose→confirm guardrails) | `app/actions.py` | v0.15 |
| **Security**: injection defence, token vault, scope audit | `app/security.py` | v0.16 |
| **Progress/habit dashboard** | `/progress` + `frontend/app/progress` | v0.17 |
| **Study-material RAG** assistant | `app/intelligence/rag.py` | v0.18 |
| **Kairo Greek Theme & Responsive UI** (Light/Dark mode) | `frontend/` | v0.18+ |
| Offline **evaluation** + significance + red-team | `eval/` | v0.7–0.16 |

**Key API Endpoints:** `/briefing` · `/schedule` · `/opportunities` (+`/status`) · `/chat` · `/progress` · `/actions/propose` (+`/confirm`) · `/feedback` · `/stats` · `/notify/preview` (+`/send`) · `/study/ask` · `/tools` · `/health`.

---

## The Research Benchmark

Evaluated across **40 labeled student scenarios** representing exam weeks, placement seasons, deadline clusters, and noise:
- The learned ranker scores **nDCG@5 = 0.968** on unseen scenarios (leave-one-out cross-validation) vs **0.887** for traditional due-date sorting — a statistically significant margin (Wilcoxon paired signed-rank test $p \approx 2 \times 10^{-5}$, effect size $r \approx 0.74$).
- The indirect prompt-injection filter neutralizes **100%** of an adversarial red-team dataset with **0%** false positive degradation on benign academic text.
- Full details, ablation results, and threats-to-validity are in `docs/EVALUATION.md`.

---

## Project Layout

```
kairo/
├─ backend/
│  ├─ app/
│  │  ├─ main.py              FastAPI entrypoint (all endpoints)
│  │  ├─ config.py schemas.py cache.py store.py security.py notifier.py actions.py
│  │  ├─ orchestrator/        mcp_manager · prioritizer · ranking · llm · agent
│  │  └─ intelligence/        features · train · learned_ranker · scheduler · opportunities · rag
│  ├─ mcp_servers/            github · gmail · calendar · codeforces · classroom · common
│  ├─ eval/                   metrics · rankers · stats · datasets · run_eval · security_eval
│  ├─ tests/                  66 passing unit & integration tests
│  └─ demo.py
├─ frontend/                  Next.js dashboard (Parian Light / Aegean Dark) + Oracle Chat + Progress
├─ docs/                      ARCHITECTURE · SETUP · ROADMAP · EVALUATION · GUIDE.html · PRODUCT_PLAN
├─ releases/                  versioned release archives v0.1.0 → v0.18.0
└─ CHANGELOG.md               version history
```

---

## Team

Nancy Singh (23/IT/108) · Priyanshu Jha (23/IT/122) · Nimish Aggarwal (23/IT/111)  
Guide: Dr. Varsha Sisaudia, Information Technology.
