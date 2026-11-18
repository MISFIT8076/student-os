"""'What should I do today?' endpoint."""
from __future__ import annotations

from fastapi import APIRouter

from app.orchestrator import mcp_manager
from app.orchestrator.agent import build_briefing
from app.schemas import Briefing, ToolInfo

router = APIRouter(tags=["briefing"])


@router.get("/briefing", response_model=Briefing)
async def get_briefing(refresh: bool = False) -> Briefing:
    """Fan out across all MCP servers, rank everything, return the day plan.

    Pass ?refresh=true to bypass the cache and force a fresh fetch.
    """
    return await build_briefing(force_refresh=refresh)


@router.get("/tools", response_model=list[ToolInfo])
async def get_tools() -> list[ToolInfo]:
    """Discover every tool currently exposed by connected MCP servers."""
    return await mcp_manager.list_all_tools()
