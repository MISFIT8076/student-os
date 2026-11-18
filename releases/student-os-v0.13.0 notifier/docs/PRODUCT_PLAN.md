# Student OS — Product & Technical Master Plan

*How we turn a working integration into a genuinely useful, research-grade
final-year IT project — designed from the student's point of view.*

This plan takes the platform we already have (5 MCP connectors, an orchestrator, a rule-based prioritizer, a caching layer, an evaluation harness) and layers on
the things a real student actually needs. Every feature below is justified by a
student need, not by "it's cool tech."

> **Status (v0.13.0):** learning-to-rank, NLP deadline extraction, persistence + feedback, day-scheduler + pacing, proactive notifier are
> implemented and tested. The remaining items are listed as future work below.

---

## 1. Who we're building for (put yourself in their shoes)

**Persona — "Aarav", 4th-year IT student.** Placement season. He's chasing
internships, keeping up with coursework, doing DSA practice, and running his
FYP. His pain isn't a lack of apps — it's the *mental tax* of stitching 8 apps
together every morning and the fear of missing the one email that mattered.

**Jobs-to-be-done (the north star):** (1) *Tell me what matters now*, (2) *don't
let me miss anything*, (3) *help me fit it into my day*, (4) *surface
opportunities*, (5) *let me act quickly*, (6) *show me I'm on track*, (7) *keep
me safe and calm*.

---

## 2. Feature modules (MoSCoW prioritized)

### MUST-HAVE — the core contribution + essentials

- **⭐ Personalized learning-to-rank prioritizer.** Replace fixed weights with a
  model that learns priorities from actions (opened, done, dismissed, snoozed). ✅ **Done.**
- **⭐ NLP deadline & task extraction.** Detect deadlines buried in email
  and Classroom text. ✅ **Done.**
- **Persistence + feedback loop.** Store item history, user actions,
  and learned preferences. ✅ **Done.**
- **⭐ Security & privacy layer.** Least-privilege scopes, encrypted
  token vault, prompt-injection sanitizer.
- **Offline evaluation + user study.** Extend the benchmark;
  run a 2-week study with ~15 students. ✅ **Done.**

### SHOULD-HAVE — high student value, achievable

- **⭐ Intelligent day-scheduler.** Turn the ranked list into a time-blocked plan. ✅ **Done.**
- **Proactive daily brief + reminders.** Push the brief to Telegram/email. ✅ **Done.**
- **Opportunity radar.** Aggregate internships, scholarships, hackathons.
- **Action layer with guardrails.** Safe write-actions with confirmation.

### COULD-HAVE — stretch, if time allows

- **Progress & habit dashboard.** Streaks, action counts, application funnel.
- **Study-material assistant (RAG).** Index notes and answer questions.
- **Wellbeing-aware pacing.** Detect over-commitment and suggest a realistic day. ✅ **Done.**

---

## One-line thesis

> **Student OS: a personalized, learning-based prioritization-and-planning agent
> over heterogeneous student data streams (via the Model Context Protocol),
> with NLP deadline extraction
> — evaluated with an offline ranking benchmark and a two-week user study.**

---

## Team split (3-person)

| Member | Owns | Key deliverables |
| --- | --- | --- |
| **M1 — Platform & Data** | MCP servers, OAuth, persistence, notifier, deployment | reliable data layer + push notifications |
| **M2 — Intelligence** | NLP extractor, feature builder, learning-to-rank, scheduler, experiments | the research core + results |
| **M3 — Product & Study + Security** | frontend, action layer, security, user study | usable app + evidence + trust |
