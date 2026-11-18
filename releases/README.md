# Releases — Student OS, version by version

Each `.zip` here is a snapshot of the project as it grew, one feature per
version. The number prefix keeps them in order. Unzip any archive to see the
codebase at that stage; open its `VERSION.txt` for a one-line summary.

| # | Archive | What this version adds |
| --- | --- | --- |
| 01 | `student-os-v0.1.0-initial-platform.zip` | Orchestrator, 3 MCP servers (GitHub/Gmail/Calendar), rule-based prioritizer, FastAPI, mock mode |
| 02 | `student-os-v0.2.0-web-app.zip` | Next.js + TypeScript dashboard and chat UI |
| 03 | `student-os-v0.3.0-codeforces.zip` | Codeforces MCP server (real public API) |
| 04 | `student-os-v0.4.0-google-oauth.zip` | Shared Google OAuth; real Gmail + Calendar |
| 05 | `student-os-v0.5.0-caching.zip` | Caching layer (Redis + in-memory fallback) |
| 06 | `student-os-v0.6.0-classroom.zip` | Google Classroom MCP server |
| 07 | `student-os-v0.7.0-evaluation-harness.zip` | Ranking metrics, baselines, evaluation runner |
| 08 | `student-os-v0.8.0-dataset-and-significance.zip` | 40-scenario dataset + Wilcoxon significance test |
| 09 | `student-os-v0.9.0-documentation.zip` | Documentation formalized + CHANGELOG added |
| 10 | `student-os-v0.10.0-learned-ranker.zip` | Learned-to-rank model + persistence + feedback loop |
| 11 | `student-os-v0.11.0-deadline-extraction.zip` | NLP deadline extraction from email/announcement text |
| 12 | `student-os-v0.12.0-day-scheduler.zip` | Intelligent day-scheduler + wellbeing-aware pacing |
| 13 | `student-os-v0.13.0-notifier.zip` | Proactive notifier (Telegram/email + dry-run) |
| 14 | `student-os-v0.14.0-opportunity-radar.zip` | Opportunity radar + application tracking |
| 15 | `student-os-v0.15.0-action-layer.zip` | Action layer with propose/confirm guardrails |
| 16 | `student-os-v0.16.0-security.zip` | Security hardening (prompt-injection defence, token vault, scope audit) |
| 17 | `student-os-v0.17.0-progress-dashboard.zip` | Progress & habit dashboard |
| 18 | `student-os-v0.18.0-rag-assistant.zip` | Study-material RAG assistant |

The file count grows every version (36 → 101 files), which visualises the
incremental build.

**Documentation is in every archive.** The `README.md` and the full `docs/` set
(including `GUIDE.html`) are bundled into *every* version snapshot as living
documentation (current content), so any archive you open is self-explanatory.

## How to read these

These are **feature snapshots**: the files present in each archive reflect what
existed at that version, so you can see exactly which module arrived when (e.g.
`eval/` first appears in v0.7.0, `app/intelligence/` in v0.10.0). Each archive's
`servers.json` and `requirements.txt` are generated to match that version.

The newest archive (**v0.10.0**) is the canonical, fully runnable project;
earlier archives are primarily for demonstrating the progression. Shared "wiring"
files carry their latest content.

## Regenerating

```bash
cd student-os
python tools/make_release_zips.py     # rewrites releases/*.zip from the manifest
```
