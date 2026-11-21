"""Opportunity radar endpoints: list opportunities and track application status."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from app import store
from app.auth import get_optional_current_user
from app.orchestrator.agent import build_opportunities
from app.schemas import OpportunityStatusRequest

router = APIRouter(tags=["opportunities"])


@router.get("/opportunities")
async def get_opportunities(
    current_user: Optional[dict] = Depends(get_optional_current_user),
) -> list[dict]:
    user_id = current_user["id"] if current_user else None
    return await build_opportunities(user_id=user_id)


@router.post("/opportunities/status")
def set_status(req: OpportunityStatusRequest) -> dict:
    try:
        ok = store.set_opportunity_status(
            req.source, req.title, req.due, req.kind, req.otype, req.status
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"ok": ok}
