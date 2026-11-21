"""Conversational endpoint: natural-language questions over connected data."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends

from app.auth import get_optional_current_user
from app.orchestrator.agent import handle_chat
from app.schemas import ChatRequest, ChatResponse

router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def post_chat(
    req: ChatRequest,
    current_user: Optional[dict] = Depends(get_optional_current_user),
) -> ChatResponse:
    user_id = current_user["id"] if current_user else None
    return await handle_chat(req.message, user_id=user_id)
