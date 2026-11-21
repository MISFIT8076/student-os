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
from app.schemas import ActionItem, Briefing, ChatResponse, Priority


def _blend_custom_and_filter_done(items: list[ActionItem], sources: list[str]) -> list[ActionItem]:
    """Incorporate custom user tasks and remove any items marked done."""
    custom_rows = store.get_active_custom_tasks()
    for row in custom_rows:
        try:
            p = Priority(row.get("priority", "medium"))
        except ValueError:
            p = Priority.medium
        score_map = {"urgent": 10.0, "high": 7.0, "medium": 4.0, "low": 1.5}
        base_score = score_map.get(p.value, 4.0)
        items.append(
            ActionItem(
                source=row.get("source", "personal"),
                kind=row.get("kind", "task"),
                title=row.get("title", ""),
                detail=row.get("detail", ""),
                due=row.get("due"),
                priority=p,
                score=base_score,
                raw={"is_custom": True},
            )
        )
        if "personal" not in sources:
            sources.append("personal")

    done_keys = store.get_done_item_keys()
    return [it for it in items if store.item_key(it.source, it.title, it.due) not in done_keys]


async def build_briefing(force_refresh: bool = False) -> Briefing:
    items, sources, _tools, cached = await mcp_manager.gather_action_items(force_refresh)
    items = _blend_custom_and_filter_done(items, sources)
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
    items, sources, tools, _cached = await mcp_manager.gather_action_items()
    items = _blend_custom_and_filter_done(items, sources)
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
    items, sources, _tools, _cached = await mcp_manager.gather_action_items()
    items = _blend_custom_and_filter_done(items, sources)
    _name, rank_fn = get_ranker()
    ranked = rank_fn(items)
    return schedule_day(ranked, date.today())


async def build_opportunities() -> list[dict]:
    """Gather items and surface the ones worth tracking (with saved status)."""
    items, _sources, _tools, _cached = await mcp_manager.gather_action_items()
    return collect_opportunities(items)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
