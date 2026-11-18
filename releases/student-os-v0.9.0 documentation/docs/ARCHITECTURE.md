# Architecture

Student OS keeps the layered MCP design from the proposal. This document is current as of
**v0.9.0**.

```
Student (natural-language input)
        │
        ▼
FRONTEND  (Next.js: dashboard · chat)      ← frontend/
        │  HTTP
        ▼
BACKEND API (FastAPI)                                  ← app/main.py
  /briefing /chat /tools /health
        │
        ▼
ORCHESTRATOR (tool router)                             ← app/orchestrator/mcp_manager.py
  • launches MCP servers over stdio, lists+calls tools
  • normalizes to ActionItem, de-duplicates, CACHES     ← app/cache.py
        │
        ├── GitHub · Gmail · Calendar · Codeforces · Classroom  ← mcp_servers/*
        │        (each wraps a real API; mock fallback)
        ▼
LLM writer (Claude) or deterministic fallback          ← app/orchestrator/llm.py
```

## Request flow: "What should I do today?"

1. **API** — `GET /briefing` calls `agent.build_briefing()`.
2. **Fan-out (cached)** — `mcp_manager.gather_action_items()` reads
   `servers.json`, launches each enabled server as a subprocess over **stdio**,
   calls `initialize`, `list_tools`, then every tool. Results are cached briefly
   (`app/cache.py`) so repeat calls are instant.
3. **Normalize** — each tool returns `ActionItem`-shaped rows.
   The manager maps to `ActionItem` models and de-duplicates.
4. **Rank** — the `prioritizer` scores items by kind, due-proximity, and
   context (exam week, internship category, noise detection) and sorts them.
5. **Summarize** — `llm.write_briefing()` writes a headline + summary. With `ANTHROPIC_API_KEY` set it uses Claude, else a
   deterministic writer.
6. **Respond** — a `Briefing` is returned and rendered by the dashboard.

## The `ActionItem` contract

Every server, regardless of platform, emits rows with these keys — the shared
shape that lets the ranker compare a PR against an email against an exam:

| key | meaning |
| --- | --- |
| `kind` | type within the source: `pull_request`, `email`, `deadline`, `exam`, `event`, `issue`, `notification`, `contest`, `practice`, `announcement` |
| `title` | one-line label shown to the student |
| `detail` | secondary context (repo/#, sender, location) |
| `url` | deep link (optional) |
| `due` | ISO date (optional) |
| `extra` | source metadata (e.g. `{"category": "internship"}`) |

## Layer responsibilities

* **MCP servers** (`mcp_servers/`) — one per platform; wrap a real API with a
  mock fallback; read-only. Shared helpers live in `common/` (OAuth).
* **Orchestrator** (`app/orchestrator/`) — fan-out, dedupe, cache, ranking
  selection, LLM writing.

## Design principles

* **Isolation** — a failing/slow server is skipped; the briefing still works.
* **Graceful degradation** — no credentials, no LLM key, no Redis?
  Each falls back (mock data / deterministic writer / in-memory cache) so the app
  always runs.
* **Reuse** — servers are standard MCP; they work in any MCP client.

## Adding a new MCP server (still a one-file change)

1. Create `mcp_servers/<x>_server/server.py` — copy `github_server`.
2. Return `ActionItem`-shaped dicts from each `@mcp.tool()`.
3. Register it in `backend/servers.json`.
4. Done — orchestrator, ranker, API, and UI need no changes. (Codeforces and
   Classroom were added exactly this way.)
