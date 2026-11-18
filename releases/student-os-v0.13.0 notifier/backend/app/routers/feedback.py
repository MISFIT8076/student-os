"""Feedback + stats endpoints — the loop that lets the ranker learn.

POST /feedback  — record what the student did with an item.
GET  /stats     — aggregate counts for the progress dashboard.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app import store
from app.schemas import FeedbackRequest

router = APIRouter(tags=["feedback"])


@router.post("/feedback")
def post_feedback(req: FeedbackRequest) -> dict:
    try:
        ok = store.record_feedback(req.source, req.kind, req.title, req.due, req.action)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"ok": ok}


@router.get("/stats")
def get_stats() -> dict:
    return store.get_stats()


@router.get("/progress")
def get_progress() -> dict:
    """Habit + progress aggregates: done-streak, action counts, application funnel."""
    return store.get_progress()
