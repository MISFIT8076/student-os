"""Day-plan endpoint: a time-blocked schedule built from the ranked items."""
from __future__ import annotations

from fastapi import APIRouter

from app.orchestrator.agent import build_schedule

router = APIRouter(tags=["schedule"])


@router.get("/schedule")
async def get_schedule() -> dict:
    return await build_schedule()
