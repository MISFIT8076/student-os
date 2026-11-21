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


def _blend_custom_and_filter_done(
    items: list[ActionItem], sources: list[str]
) -> list[ActionItem]:
    """Helper to merge active user-created custom tasks and filter out completed tasks."""
    try:
        tasks = []
        if hasattr(store, "get_active_custom_tasks"):
            tasks = store.get_active_custom_tasks()
        elif hasattr(store, "list_custom_tasks"):
            tasks = store.list_custom_tasks(include_done=False)

        for t in tasks:
            try:
                p = Priority(t["priority"].lower())
            except Exception:
                p = Priority.medium

            items.append(
                ActionItem(
                    source=t.get("source", "personal"),
                    kind=t.get("kind", "task"),
                    title=t.get("title", "(untitled)"),
                    detail=t.get("detail") or "",
                    url=t.get("url"),
                    due=t.get("due"),
                    priority=p,
                    raw={"estimated_minutes": t.get("estimated_minutes")},
                )
            )
            if "personal" not in sources:
                sources.append("personal")
    except Exception as exc:
        import logging
        logging.getLogger(__name__).warning("Failed to blend custom tasks: %s", exc)

    try:
        done_keys = store.get_done_item_keys()
        return [it for it in items if store.item_key(it.source, it.title, it.due) not in done_keys]
    except Exception:
        return items


async def build_briefing(force_refresh: bool = False, user_id: int | None = None) -> Briefing:
    items, sources, _tools, cached = await mcp_manager.gather_action_items(force_refresh, user_id=user_id)
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


async def handle_chat(message: str, user_id: int | None = None) -> ChatResponse:
    items, sources, tools, _cached = await mcp_manager.gather_action_items(user_id=user_id)
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


async def build_schedule(user_id: int | None = None) -> dict:
    """Gather, rank, and time-block today into an actual plan."""
    items, sources, _tools, _cached = await mcp_manager.gather_action_items(user_id=user_id)
    items = _blend_custom_and_filter_done(items, sources)
    _name, rank_fn = get_ranker()
    ranked = rank_fn(items)
    return schedule_day(ranked, date.today())


async def build_opportunities(user_id: int | None = None) -> list[dict]:
    """Gather items and surface the ones worth tracking (with saved status)."""
    items, _sources, _tools, _cached = await mcp_manager.gather_action_items(user_id=user_id)
    return collect_opportunities(items)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
