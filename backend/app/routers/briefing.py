"""'What should I do today?' endpoint."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends

from app.auth import get_optional_current_user
from app.orchestrator import mcp_manager
from app.orchestrator.agent import build_briefing
from app.schemas import Briefing, ToolInfo

router = APIRouter(tags=["briefing"])


@router.get("/briefing", response_model=Briefing)
async def get_briefing(
    refresh: bool = False,
    current_user: Optional[dict] = Depends(get_optional_current_user),
) -> Briefing:
    """Fan out across all MCP servers, rank everything, return the day plan.

    Pass ?refresh=true to bypass the cache and force a fresh fetch.
    """
    user_id = current_user["id"] if current_user else None
    return await build_briefing(force_refresh=refresh, user_id=user_id)


@router.get("/tools", response_model=list[ToolInfo])
async def get_tools(
    current_user: Optional[dict] = Depends(get_optional_current_user),
) -> list[ToolInfo]:
    """Discover every tool currently exposed by connected MCP servers."""
    user_id = current_user["id"] if current_user else None
    return await mcp_manager.list_all_tools(user_id=user_id)
