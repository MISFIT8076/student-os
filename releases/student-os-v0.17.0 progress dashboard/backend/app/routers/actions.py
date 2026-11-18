"""Action endpoints: propose an action (preview + token), then confirm it."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app import actions
from app.schemas import ConfirmActionRequest, ProposeActionRequest

router = APIRouter(tags=["actions"])


@router.post("/actions/propose")
def propose(req: ProposeActionRequest) -> dict:
    try:
        return actions.propose(req.action, req.source, req.kind, req.title, req.due)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/actions/confirm")
def confirm(req: ConfirmActionRequest) -> dict:
    try:
        return actions.confirm(req.token)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
