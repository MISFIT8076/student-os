"""Opportunity radar endpoints: list opportunities and track application status."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app import store
from app.orchestrator.agent import build_opportunities
from app.schemas import OpportunityStatusRequest

router = APIRouter(tags=["opportunities"])


@router.get("/opportunities")
async def get_opportunities() -> list[dict]:
    return await build_opportunities()


@router.post("/opportunities/status")
def set_status(req: OpportunityStatusRequest) -> dict:
    try:
        ok = store.set_opportunity_status(
            req.source, req.title, req.due, req.kind, req.otype, req.status
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"ok": ok}
