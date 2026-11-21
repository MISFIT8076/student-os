"""LLM wrapper with an offline fallback.

If ANTHROPIC_API_KEY is set (and not in mock mode) the briefing headline/summary
and chat replies are written by a real model. Otherwise a deterministic,
rule-based writer produces perfectly usable text — so the app is fully
demonstrable with no API key.
"""
from __future__ import annotations

from collections import Counter

from app.config import get_settings
from app.schemas import ActionItem, Priority, ToolInfo
from app.security import safe_text


def llm_available() -> bool:
    return get_settings().llm_enabled


# ── deterministic writers (always available) ───────────────────────────────
def _fallback_briefing(items: list[ActionItem], exam_week: bool) -> tuple[str, str]:
    if not items:
        return "You're all clear.", "Nothing urgent surfaced across your connected platforms."

    urgent = [i for i in items if i.priority == Priority.urgent]
    high = [i for i in items if i.priority == Priority.high]
    top = items[0]

    counts = Counter(i.kind for i in items[:6])
    kinds_phrase = ", ".join(f"{n} {k.replace('_', ' ')}" for k, n in counts.items())

    headline = (
        f"{len(urgent) or len(high)} thing(s) need attention first"
        + (" — exam week, so coursework is boosted." if exam_week else ".")
    )
    lead = f"Start with: {top.title}"
    if top.due:
        lead += f" (due {top.due})"
    summary = (
        f"{lead}. Across your platforms today: {kinds_phrase}. "
        + ("Focus on graded work; competitive practice is de-prioritized this week."
           if exam_week else
           "Deadlines are ranked above everything else, then reviews and opportunities.")
    )
    return headline, summary


def _fallback_chat(message: str, tools: list[ToolInfo], items: list[ActionItem]) -> str:
    msg = message.lower()
    
    # Priority & Opportune moment synthesis
    if any(w in msg for w in ("priority", "#1", "first", "start", "what should i do")):
        if items:
            top = items[0]
            due_str = f" (due {top.due})" if top.due else ""
            second = f"\n• Follow-up: {items[1].title}" if len(items) > 1 else ""
            return (
                f"🏛️ **The Opportune Moment (Kairos):**\n\n"
                f"Your #1 focus right now is **{top.title}** [{top.source.upper()}]{due_str}.\n\n"
                f"💡 **Recommendation:** Lock in a 45-minute deep focus block now before addressing lower-priority interruptions.{second}"
            )
        return "You have no active urgent tasks right now. Use this time for forward preparation or rest."

    # Study block planning
    if any(w in msg for w in ("plan", "focus", "block", "schedule", "study")):
        if items:
            top_items = items[:3]
            plan_lines = "\n".join([f"• **Session {idx+1} ({45}m):** {item.title}" for idx, item in enumerate(top_items)])
            return (
                f"⏱️ **Synthesized Focus Block:**\n\n"
                f"{plan_lines}\n\n"
                f"⚡ Interleave with 10-minute rest intervals to sustain peak cognitive endurance."
            )
        return "Your queue is clear. I recommend a 90-minute open exploration block."

    # GitHub / Code reviews
    if any(w in msg for w in ("github", "pr", "pull request", "issue", "review")):
        picks = [i for i in items if i.source == "github"]
        if picks:
            lines = [f"• **{i.title}**" + (f" — due {i.due}" if i.due else "") for i in picks[:5]]
            return f"⑂ **Active GitHub Deliverables ({len(picks)}):**\n" + "\n".join(lines)
        return "No pending GitHub PRs or code reviews requiring your immediate attention."

    # Emails & Career notices
    if any(w in msg for w in ("email", "mail", "internship", "job", "career")):
        picks = [i for i in items if i.source == "gmail"]
        if picks:
            lines = [f"• **{i.title}**" + (f" — {i.detail}" if i.detail else "") for i in picks[:5]]
            return f"📬 **Relevant Email Announcements ({len(picks)}):**\n" + "\n".join(lines)
        return "No unread critical emails or internship announcements found in your recent sync."

    # Exams & Deadlines
    if any(w in msg for w in ("deadline", "calendar", "exam", "due", "today", "countdown")):
        picks = [i for i in items if i.due or i.source in ("calendar", "canvas")]
        if picks:
            lines = [f"• **{i.title}**" + (f" — *due {i.due}*" if i.due else "") for i in picks[:5]]
            return f"🎓 **Approaching Deadlines & Calendar Events:**\n" + "\n".join(lines)
        return "No hard deadlines recorded for today. Great job staying ahead of your schedule!"

    # Default overview
    picks = items[:4]
    if not picks:
        tool_names = ", ".join(sorted({t.server for t in tools})) or "no servers"
        return (
            "I am the Oracle of Kairo. Connected platforms: "
            f"{tool_names}. Ask me 'What is my top priority?' or 'Plan a 2-hour study block'."
        )
    lines = [f"• **{i.title}** [{i.source}]" + (f" — due {i.due}" if i.due else "") for i in picks]
    return "🏛️ **Kairo Context Overview:**\n" + "\n".join(lines)


# ── real LLM (optional) ─────────────────────────────────────────────────────
def _items_as_context(items: list[ActionItem]) -> str:
    rows = []
    for i in items[:20]:
        # Item text comes from untrusted sources (emails, tool output), so it is
        # sanitized against prompt-injection before being shown to the model.
        title = safe_text(i.title)
        detail = safe_text(i.detail)
        rows.append(
            f"- [{i.priority.value}] ({i.source}/{i.kind}) {title}"
            + (f" | due {i.due}" if i.due else "")
            + (f" | {detail}" if detail else "")
        )
    return "\n".join(rows)


def _gemini_text(system: str, user: str) -> str | None:
    settings = get_settings()
    if not settings.gemini_api_key:
        return None
    import sys
    import httpx

    configured = settings.gemini_model.strip()
    # Ordered fallback cascade: configured model first, followed by resilient models
    candidates: list[str] = [configured]
    for fallback in [
        "gemini-flash-lite-latest",
        "gemini-3.5-flash-lite",
        "gemini-3-flash-preview",
    ]:
        if fallback not in candidates and fallback != configured:
            candidates.append(fallback)

    for cand in candidates:
        model = cand if cand.startswith("models/") else f"models/{cand}"
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/"
            f"{model}:generateContent?key={settings.gemini_api_key}"
        )
        payload = {
            "system_instruction": {"parts": [{"text": system}]},
            "contents": [{"role": "user", "parts": [{"text": user}]}],
            "generationConfig": {"temperature": 0.4, "maxOutputTokens": 800},
        }
        try:
            with httpx.Client(timeout=20) as client:
                resp = client.post(url, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    candidates_out = data.get("candidates", [])
                    if candidates_out and "content" in candidates_out[0]:
                        parts = candidates_out[0]["content"].get("parts", [])
                        if parts and "text" in parts[0]:
                            return parts[0]["text"]
                else:
                    print(
                        f"[Oracle/LLM] Model {model} returned {resp.status_code}: {resp.text[:100]}",
                        file=sys.stderr,
                    )
        except Exception as exc:
            print(f"[Oracle/LLM] Request to {model} failed: {exc}", file=sys.stderr)
            continue

    return None


def _anthropic_text(system: str, user: str) -> str | None:
    settings = get_settings()
    if not settings.anthropic_api_key:
        return None
    try:
        import anthropic

        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        resp = client.messages.create(
            model=settings.llm_model,
            max_tokens=600,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return "".join(b.text for b in resp.content if getattr(b, "type", "") == "text")
    except Exception:  # noqa: BLE001 — any failure falls back to deterministic
        return None


def _call_llm(system: str, user: str) -> str | None:
    settings = get_settings()
    if settings.gemini_api_key:
        res = _gemini_text(system, user)
        if res:
            return res
    if settings.anthropic_api_key:
        return _anthropic_text(system, user)
    return None


def write_briefing(items: list[ActionItem], exam_week: bool) -> tuple[str, str]:
    if not llm_available():
        return _fallback_briefing(items, exam_week)
    system = (
        "You are Kairo, an assistant inspired by the Greek concept of Kairos (the opportune moment) "
        "that helps an engineering student decide what to do today. Be concise and concrete. Return two lines: "
        "first line a punchy headline, then a 2-3 sentence summary."
    )
    user = (
        f"Exam week: {exam_week}. Ranked items across the student's platforms:\n"
        f"{_items_as_context(items)}\n\nWrite the headline and summary."
    )
    text = _call_llm(system, user)
    if not text:
        return _fallback_briefing(items, exam_week)
    lines = [l for l in text.splitlines() if l.strip()]
    headline = lines[0] if lines else "Your day at a glance"
    summary = " ".join(lines[1:]) if len(lines) > 1 else headline
    return headline, summary


def chat_reply(message: str, tools: list[ToolInfo], items: list[ActionItem]) -> str:
    if not llm_available():
        return _fallback_chat(message, tools, items)
    system = (
        "You are Kairo (Oracle of the Opportune Moment). Answer using ONLY the context items provided, "
        "which were gathered from the student's connected MCP servers. "
        "Be concise and actionable."
    )
    user = (
        f"Student asked: {message}\n\n"
        f"Available tools: {', '.join(t.server + '.' + t.name for t in tools)}\n\n"
        f"Context items:\n{_items_as_context(items)}"
    )
    text = _call_llm(system, user)
    return text or _fallback_chat(message, tools, items)
