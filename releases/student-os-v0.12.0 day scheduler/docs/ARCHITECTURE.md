# Architecture

Student OS keeps the layered MCP design from the proposal and adds an
intelligence layer (learning, extraction, scheduling), a persistence + feedback
loop. This document is current as of
**v0.12.0**.

```
Student (natural-language input)
        │
        ▼
FRONTEND  (Next.js: dashboard · chat)      ← frontend/
        │  HTTP
        ▼
BACKEND API (FastAPI)                                  ← app/main.py
  /briefing /chat /tools /health /feedback /stats /schedule
        │
        ▼
ORCHESTRATOR (tool router)                             ← app/orchestrator/mcp_manager.py
  • launches MCP servers over stdio, lists+calls tools
  • normalizes to ActionItem, de-duplicates, CACHES     ← app/cache.py
        │
        ├── GitHub · Gmail · Calendar · Codeforces · Classroom  ← mcp_servers/*
        │        (each wraps a real API; mock fallback)
        │        Gmail/Classroom text → DEADLINE EXTRACTION      ← mcp_servers/common/extraction.py
        ▼
INTELLIGENCE                                           ← app/intelligence/
  • ranking: rule-based baseline OR learned model       ← ranking.py · learned_ranker.py · prioritizer.py
  • scheduler (time-blocks the day, wellbeing pacing)    ← scheduler.py
        │
        ▼
LLM writer (Claude) or deterministic fallback          ← app/orchestrator/llm.py
        │
        ▼
PERSISTENCE (SQLite/Postgres): shown items + feedback  ← app/store.py
```

## Request flow: "What should I do today?"

1. **API** — `GET /briefing` calls `agent.build_briefing()`.
2. **Fan-out (cached)** — `mcp_manager.gather_action_items()` reads
   `servers.json`, launches each enabled server as a subprocess over **stdio**,
   calls `initialize`, `list_tools`, then every tool. Results are cached briefly
   (`app/cache.py`) so repeat calls are instant.
3. **Normalize + extract** — each tool returns `ActionItem`-shaped rows; Gmail
   and Classroom additionally run **deadline extraction** so due dates hidden in
   text are recovered.
   The manager maps to `ActionItem` models and de-duplicates.
4. **Rank** — `ranking.get_ranker()` picks the ranker from config: the
   rule-based `prioritizer` (baseline / cold-start) or the trained
   `LearnedRanker`. Both produce a sorted list.
5. **Summarize** — `llm.write_briefing()` writes a headline + summary. With `ANTHROPIC_API_KEY` set it uses Claude, else a
   deterministic writer.
6. **Log + respond** — the shown items are recorded to the store (feedback loop),
   and a `Briefing` is returned and rendered by the dashboard.

Other flows reuse steps 2–4: `/schedule` feeds the ranked list into the
scheduler; `/chat` routes a
question over the same context.

## The `ActionItem` contract

Every server, regardless of platform, emits rows with these keys — the shared
shape that lets the ranker compare a PR against an email against an exam:

| key | meaning |
| --- | --- |
| `kind` | type within the source: `pull_request`, `email`, `deadline`, `exam`, `event`, `issue`, `notification`, `contest`, `practice`, `announcement` |
| `title` | one-line label shown to the student |
| `detail` | secondary context (repo/#, sender, location) |
| `url` | deep link (optional) |
| `due` | ISO date (optional); may be **extracted** from text |
| `extra` | source metadata (e.g. `{"category": "internship", "due_source": "extracted"}`) |

## Layer responsibilities

* **MCP servers** (`mcp_servers/`) — one per platform; wrap a real API with a
  mock fallback; read-only. Shared helpers live in `common/` (OAuth, extraction).
* **Orchestrator** (`app/orchestrator/`) — fan-out, dedupe, cache, ranking
  selection, LLM writing.
* **Intelligence** (`app/intelligence/`) — the learnable/algorithmic parts:
  feature builder, trained ranker, scheduler.
* **Persistence** (`app/store.py`) — SQLAlchemy over SQLite (default) or Postgres
  (`DATABASE_URL`); logs shown items + feedback; powers learning.

## Design principles

* **Isolation** — a failing/slow server is skipped; the briefing still works.
* **Graceful degradation** — no credentials, no LLM key, no Redis, no DB write?
  Each falls back (mock data / deterministic writer / in-memory cache) so the app
  always runs.
* **Reuse** — servers are standard MCP; they work in any MCP client.
* **Pluggability** — the ranker is swappable (`RANKER=rule|learned`); the cache
  and DB back-ends are swappable via env.

## Adding a new MCP server (still a one-file change)

1. Create `mcp_servers/<x>_server/server.py` — copy `github_server`.
2. Return `ActionItem`-shaped dicts from each `@mcp.tool()`.
3. Register it in `backend/servers.json`.
4. Done — orchestrator, ranker, API, and UI need no changes. (Codeforces and
   Classroom were added exactly this way.)
