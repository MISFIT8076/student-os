# Roadmap & feasibility notes

This maps the code you have now onto your proposal's 5-phase timeline, and
flags the things the proposal doesn't (yet) acknowledge. Read the feasibility
section before you commit to LinkedIn or LeetCode.

## Where this scaffold puts you

| Proposal phase | Status in this repo |
| --- | --- |
| Phase 1 — architecture + OAuth setup | Architecture done; layered MCP design implemented. OAuth still to wire. |
| Phase 2 — Email, Calendar, GitHub servers + orchestrator | Orchestrator + GitHub (real) done. Email/Calendar are working mock servers awaiting OAuth. |
| Phase 3 — LeetCode/Classroom/LinkedIn + Daily Briefing | Daily Briefing **done**. Codeforces (instead of LeetCode) and Classroom **done**. LinkedIn: use the Gmail route — see feasibility below. |
| Phase 4 — React dashboard + context-aware prioritization | Dashboard + chat done. Context-aware prioritizer done and unit-tested. |
| Phase 5 — testing, security, docs | Prioritizer tests + these docs done; security hardening still to do. |

You are effectively starting mid-Phase 3 with a demonstrable end-to-end system.

## API feasibility — read this before scoping

Not every platform in the proposal has a usable API. Plan around this:

* **GitHub** — official REST API. ✅ Done.
* **Google Calendar / Gmail** — official APIs, OAuth. ✅ **Implemented** (shared
  read-only OAuth; see `docs/SETUP.md` §3).
* **Google Classroom** — official API exists, but course data access is
  restricted (you must be a member of the course and scopes are limited).
  ⚠️ Feasible with caveats; test early.
* **Codeforces** — official public API (`/api/`). ✅ **Implemented** (upcoming
  contests + practice reminder). Use this instead of LeetCode.
* **LeetCode** — **no official API.** Only an unofficial GraphQL endpoint that
  can break and may violate ToS. ⚠️ Treat as best-effort/optional.
* **LinkedIn** — **no open API** for reading messages or job posts, and
  scraping violates their ToS. ❌ Highest risk. Recommended substitute: detect
  LinkedIn *job/recruiter emails in Gmail* (the Gmail server already models
  this via the `internship` category) instead of hitting LinkedIn directly.

Updating the proposal to say this — and framing LinkedIn via email rather than a
direct integration — will read as maturity, not weakness, in your viva.

## Turning this into a research paper

A pure integration won't publish on its own. Attach one measurable research
question (all three align with current MCP research like MCP-Bench, ICLR 2026):

1. **Prioritization quality** — ✅ implemented in `eval/` (see
   `docs/EVALUATION.md`): labeled scenarios, nDCG@k / precision / pairwise / MRR,
   and baselines. Next: more scenarios + annotators, and add an LLM ranker as a
   second treatment.
2. **User study** — have a few students use it for 2 weeks; measure
   self-reported missed deadlines / context-switching vs a baseline week.
3. **Security of multi-server personal-data MCP** — 2026 saw 30+ MCP CVEs and
   real data-leak incidents; analyze tool-poisoning / over-broad-scope risks in
   a student-data setting and propose mitigations.

## Done since the initial scaffold

* ✅ **Codeforces MCP server** (real public API) — proved the "add a server
  without touching the core" claim: only `servers.json` + one weight changed.
* ✅ **Google OAuth** (shared, read-only) — Gmail, Calendar, and Classroom read
  live data from one token.
* ✅ **Google Classroom MCP server** — pending assignments + announcements.
* ✅ **Caching layer** (the proposal's Redis, with an in-memory fallback) — the
  fan-out is cached for a short TTL; cache hits are near-instant vs a ~6s cold
  fan-out, and `/briefing?refresh=true` forces a fresh pull.
* ✅ **Evaluation harness** (`eval/`, `docs/EVALUATION.md`) — 40 labeled
  scenarios, ranking metrics, baselines, and a **paired significance test**
  (Wilcoxon + bootstrap CI, cross-checked against scipy). The prioritizer beats
  due-date sorting significantly (p ≈ 0.0004, large effect): the measurable
  result for the paper.

## Suggested next commits

1. **Second annotator + user study.** Have ≥2 people grade the same scenarios
   (report Cohen's κ), then run the two-week **user study** — the strongest
   claim available.
2. **Security pass** — least-privilege scopes, token-at-rest handling, and a
   short threat model (aligns with the 2026 MCP-security research angle).
3. **Persist** the briefing history (the proposal's PostgreSQL) for trend charts.
4. Add a **Slack/WhatsApp notifier** so the daily briefing is pushed, not pulled.
