"""Notification endpoints: preview the daily push, or send it now."""
from __future__ import annotations

from fastapi import APIRouter

from app import notifier

router = APIRouter(tags=["notify"])


@router.get("/notify/preview")
async def preview() -> dict:
    return {"preview": await notifier.build_preview()}


@router.post("/notify/send")
async def send() -> dict:
    return await notifier.run_once()
