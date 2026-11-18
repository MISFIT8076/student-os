"""High-level agent actions used by the API routers.

build_briefing()  -> the "What should I do today?" flow
handle_chat()     -> conversational queries over the same gathered context

The ranker is pluggable (rule-based baseline or learned model), and every
non-cached briefing is logged to the store so the ranker can learn over time.
"""
from __future__ import annotations

from datetime import date, datetime, timezone

from app import store
from app.intelligence.opportunities import collect_opportunities
from app.intelligence.scheduler import schedule_day
from app.orchestrator import llm, mcp_manager
from app.orchestrator.prioritizer import _exam_week
from app.orchestrator.ranking import get_ranker
from app.schemas import Briefing, ChatResponse


async def build_briefing(force_refresh: bool = False) -> Briefing:
    items, sources, _tools, cached = await mcp_manager.gather_action_items(force_refresh)
    ranker_name, rank_fn = get_ranker()
    ranked = rank_fn(items)
    exam_week = _exam_week(ranked, date.today())
    headline, summary = llm.write_briefing(ranked, exam_week)
    if not cached:
        store.record_briefing(ranked, ranker_name)  # best-effort logging
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
    _name, rank_fn = get_ranker()
    ranked = rank_fn(items)
    reply = llm.chat_reply(message, tools, ranked)
    tool_calls = [{"server": t.server, "tool": t.name} for t in tools]
    return ChatResponse(
        reply=reply,
        tool_calls=tool_calls,
        llm_used=llm.llm_available(),
    )


async def build_schedule() -> dict:
    """Gather, rank, and time-block today into an actual plan."""
    items, _sources, _tools, _cached = await mcp_manager.gather_action_items()
    _name, rank_fn = get_ranker()
    ranked = rank_fn(items)
    return schedule_day(ranked, date.today())


async def build_opportunities() -> list[dict]:
    """Gather items and surface the ones worth tracking (with saved status)."""
    items, _sources, _tools, _cached = await mcp_manager.gather_action_items()
    return collect_opportunities(items)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
