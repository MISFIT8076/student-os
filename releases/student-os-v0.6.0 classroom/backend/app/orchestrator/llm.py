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

try:
    from app.security import safe_text
except ImportError:
    def safe_text(s: str) -> str:
        return s


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
    # Naive intent routing that mirrors what the LLM would do with tools.
    if any(w in msg for w in ("github", "pr", "pull request", "issue")):
        picks = [i for i in items if i.source == "github"]
    elif any(w in msg for w in ("email", "mail", "internship")):
        picks = [i for i in items if i.source == "gmail"]
    elif any(w in msg for w in ("deadline", "calendar", "exam", "due", "today")):
        picks = [i for i in items if i.source == "calendar"]
    else:
        picks = items[:4]

    if not picks:
        tool_names = ", ".join(sorted({t.server for t in tools})) or "no servers"
        return (
            "I couldn't find anything matching that. "
            f"Connected sources right now: {tool_names}. "
            "Try 'what should I do today?' or 'show my GitHub PRs'."
        )
    lines = [f"• {i.title}" + (f" — due {i.due}" if i.due else "") for i in picks[:5]]
    return "Here's what I found:\n" + "\n".join(lines)


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


def _anthropic_text(system: str, user: str) -> str | None:
    settings = get_settings()
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


def write_briefing(items: list[ActionItem], exam_week: bool) -> tuple[str, str]:
    if not llm_available():
        return _fallback_briefing(items, exam_week)
    system = (
        "You are Student OS, an assistant that helps an engineering student "
        "decide what to do today. Be concise and concrete. Return two lines: "
        "first line a punchy headline, then a 2-3 sentence summary."
    )
    user = (
        f"Exam week: {exam_week}. Ranked items across the student's platforms:\n"
        f"{_items_as_context(items)}\n\nWrite the headline and summary."
    )
    text = _anthropic_text(system, user)
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
        "You are Student OS. Answer using ONLY the context items provided, "
        "which were gathered from the student's connected MCP servers. "
        "Be concise and actionable."
    )
    user = (
        f"Student asked: {message}\n\n"
        f"Available tools: {', '.join(t.server + '.' + t.name for t in tools)}\n\n"
        f"Context items:\n{_items_as_context(items)}"
    )
    text = _anthropic_text(system, user)
    return text or _fallback_chat(message, tools, items)
