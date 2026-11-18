# Student OS

**An MCP-powered AI coordination layer for student life.**
BTech Final Year Project — CSE/IT. Current version: **v0.6.0**.

Instead of checking multiple apps every morning, a student asks one question —
*"What should I do today?"* — and Student OS reads across their connected
platforms (GitHub, Gmail, Calendar, Codeforces, Classroom), **ranks** everything
by importance, and presents a single prioritized plan.

It is built on the **Model Context Protocol (MCP)**: each platform is a small,
independent MCP server exposing standardized tools, and an orchestrator fans out
across them, merges, ranks, and plans.

---

## Runs immediately — no accounts needed

The whole system ships in **mock mode** (`STUDENT_OS_MOCK=true`, the default):
every server returns realistic sample data and a rule-based planner runs, so you
can demo the full pipeline before wiring a single API key, then switch pieces to
"real" one at a time.

## Quickstart

```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python demo.py                    # prints today's ranked plan (no server needed)
uvicorn app.main:app --reload     # or run the API → http://127.0.0.1:8000/docs

# Frontend (separate terminal)
cd frontend && npm install && npm run dev            # → http://localhost:3000
```

---

## What it does (feature map)

| Capability | Where | Since |
| --- | --- | --- |
| MCP orchestrator (tool router, dedupe, cache) | `app/orchestrator/mcp_manager.py` | v0.1 |
| 5 MCP servers: GitHub, Gmail, Calendar, Codeforces, Classroom | `mcp_servers/` | v0.1–0.5 |
| Context-aware **rule-based** prioritizer (baseline) | `app/orchestrator/prioritizer.py` | v0.1 |
| Caching (Redis or in-memory) | `app/cache.py` | v0.5 |
| Web dashboard + chat (Next.js/TS) | `frontend/` | v0.2+ |

**API endpoints:** `/briefing` · `/chat` · `/tools` · `/health`.

## Project layout

```
student-os/
├─ backend/
│  ├─ app/
│  │  ├─ main.py              FastAPI app (all endpoints)
│  │  ├─ config.py schemas.py cache.py
│  │  ├─ orchestrator/        mcp_manager · prioritizer · llm · agent
│  ├─ mcp_servers/            github · gmail · calendar · codeforces · classroom · common (util, google_auth)
│  ├─ tests/                  6 passing
│  └─ demo.py
├─ frontend/                  Next.js dashboard + chat
└─ README.md
```

## Status

Current version: **v0.6.0** — Google Classroom MCP server.
**6 tests passing**.

## Team

Nancy Singh (23/IT/108) · Priyanshu Jha (23/IT/122) · Nimish Aggarwal (23/IT/111)
Guide: Dr. Varsha Sisaudia, Information Technology.
