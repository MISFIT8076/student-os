# Roadmap & feasibility notes

This maps the code you have now onto your proposal's 5-phase timeline, and
flags the things the proposal doesn't (yet) acknowledge. Read the feasibility
section before you commit to LinkedIn or LeetCode.

## Where this scaffold puts you

| Proposal phase | Status in this repo |
| --- | --- |
| Phase 1 — architecture + OAuth setup | Architecture done; layered MCP design implemented. OAuth done. |
| Phase 2 — Email, Calendar, GitHub servers + orchestrator | Orchestrator + GitHub (real) done. Email/Calendar wired to real APIs via OAuth. |
| Phase 3 — LeetCode/Classroom/LinkedIn + Daily Briefing | Daily Briefing **done**. Codeforces **done**. Classroom **done**. LinkedIn: use the Gmail route — see feasibility below. |
| Phase 4 — React dashboard + context-aware prioritization | Dashboard + chat done. Context-aware prioritizer done and unit-tested. Learned ranker trained and evaluated. |
| Phase 5 — testing, security, docs | Prioritizer tests + these docs done; security hardening done. |

## API feasibility — read this before scoping

Not every platform in the proposal has a usable API. Plan around this:

* **GitHub** — official REST API. ✅ Done.
* **Google Calendar / Gmail** — official APIs, OAuth. ✅ **Implemented** (shared
  read-only OAuth; see `docs/SETUP.md` §3).
* **Google Classroom** — ✅ **Implemented**. Course data access requires membership.
* **Codeforces** — official public API. ✅ **Implemented** (upcoming contests + practice reminder).
* **LeetCode** — **no official API.** ⚠️ Treat as best-effort/optional.
* **LinkedIn** — **no open API** for reading messages or job posts. ❌ Highest risk.
  Recommended substitute: detect LinkedIn *job/recruiter emails in Gmail* instead.

## Done since the initial scaffold

* ✅ **Codeforces MCP server** (real public API) — proved the "add a server
  without touching the core" claim.
* ✅ **Google OAuth** (shared, read-only) — Gmail, Calendar, and Classroom read
  live data from one token.
* ✅ **Google Classroom MCP server** — pending assignments + announcements.
* ✅ **Caching layer** (Redis with in-memory fallback) — near-instant cache hits.
* ✅ **Evaluation harness** (`eval/`, `docs/EVALUATION.md`) — 40 labeled
  scenarios, ranking metrics, baselines, and a **paired significance test**
  (Wilcoxon + bootstrap CI).
* ✅ **Learned ranker** + persistence + feedback loop — nDCG@5 0.968.
* ✅ **Deadline extraction** — NLP parsing of dates from email/announcement text.
* ✅ **Day-scheduler** — time-blocks tasks into free slots with wellbeing pacing.
* ✅ **Proactive notifier** — Telegram/email push of daily brief + alerts.
* ✅ **Opportunity radar** — internship/scholarship/hackathon tracking.
* ✅ **Action layer** — propose→confirm guardrails for write-actions.
* ✅ **Security hardening** — prompt-injection defence, token vault, scope audit.

## Suggested next commits

1. **Progress dashboard.** Show streaks and trends.
2. **Study assistant.** RAG over notes for Q&A.
3. **User study.** Have ≥15 students use it for 2 weeks; measure
   missed deadlines and context-switching vs baseline.
