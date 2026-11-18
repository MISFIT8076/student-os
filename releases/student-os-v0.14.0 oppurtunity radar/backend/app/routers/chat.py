"""Conversational endpoint: natural-language questions over connected data."""
from __future__ import annotations

from fastapi import APIRouter

from app.orchestrator.agent import handle_chat
from app.schemas import ChatRequest, ChatResponse

router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def post_chat(req: ChatRequest) -> ChatResponse:
    return await handle_chat(req.message)
