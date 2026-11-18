"""High-level agent actions used by the API routers.

build_briefing()  -> the "What should I do today?" flow
handle_chat()     -> conversational queries over the same gathered context
"""
from __future__ import annotations

from datetime import date, datetime, timezone

from app.orchestrator import llm, mcp_manager
from app.orchestrator.prioritizer import prioritize, _exam_week
from app.schemas import Briefing, ChatResponse


async def build_briefing(force_refresh: bool = False) -> Briefing:
    items, sources, _tools, cached = await mcp_manager.gather_action_items(force_refresh)
    ranked = prioritize(items)
    exam_week = _exam_week(ranked, date.today())
    headline, summary = llm.write_briefing(ranked, exam_week)
    return Briefing(
        generated_at=_now(),
        headline=headline,
        summary=summary,
        items=ranked,
        sources_used=sources,
        llm_used=llm.llm_available(),
        cached=cached,
    )


async def handle_chat(message: str) -> ChatResponse:
    items, _sources, tools, _cached = await mcp_manager.gather_action_items()
    ranked = prioritize(items)
    reply = llm.chat_reply(message, tools, ranked)
    tool_calls = [{"server": t.server, "tool": t.name} for t in tools]
    return ChatResponse(
        reply=reply,
        tool_calls=tool_calls,
        llm_used=llm.llm_available(),
    )


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
