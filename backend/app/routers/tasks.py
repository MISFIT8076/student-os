"""Task endpoints: user task creation and completion."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app import store
from app.schemas import ActionItem, CreateTaskRequest, MarkDoneRequest, Priority

router = APIRouter(tags=["tasks"])


@router.post("/tasks", response_model=ActionItem)
def create_task(req: CreateTaskRequest) -> ActionItem:
    """Create a user-defined custom action item."""
    try:
        row = store.create_custom_task(
            title=req.title,
            detail=req.detail,
            due=req.due,
            priority=req.priority.value if hasattr(req.priority, "value") else str(req.priority),
            kind=req.kind,
            source=req.source,
        )
        score_map = {"urgent": 10.0, "high": 7.0, "medium": 4.0, "low": 1.5}
        p = req.priority
        score = score_map.get(p.value if hasattr(p, "value") else str(p), 4.0)

        return ActionItem(
            source=row["source"],
            kind=row["kind"],
            title=row["title"],
            detail=row["detail"],
            due=row["due"],
            priority=p,
            score=score,
            raw={"is_custom": True, "item_key": row["item_key"]},
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/tasks")
def list_tasks() -> list[dict]:
    """List active user-defined tasks."""
    return store.get_active_custom_tasks()


@router.post("/tasks/done")
def mark_done(req: MarkDoneRequest) -> dict:
    """Mark any task (custom or from MCP) as completed and reward the habit streak."""
    ok = store.mark_task_done(
        source=req.source,
        title=req.title,
        due=req.due,
        kind=req.kind,
    )
    return {"ok": ok}


@router.delete("/tasks/{item_key}")
def delete_task(item_key: str) -> dict:
    """Delete a custom task."""
    ok = store.delete_custom_task(item_key)
    return {"ok": ok}
