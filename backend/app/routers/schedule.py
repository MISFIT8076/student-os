"""Day-plan endpoint: a time-blocked schedule built from the ranked items."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends

from app.auth import get_optional_current_user
from app.orchestrator.agent import build_schedule

router = APIRouter(tags=["schedule"])


@router.get("/schedule")
async def get_schedule(
    current_user: Optional[dict] = Depends(get_optional_current_user),
) -> dict:
    user_id = current_user["id"] if current_user else None
    return await build_schedule(user_id=user_id)
