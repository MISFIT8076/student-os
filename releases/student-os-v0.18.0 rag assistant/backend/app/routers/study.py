"""Study-material assistant endpoint: ask questions over your notes."""
from __future__ import annotations

from fastapi import APIRouter

from app.intelligence import rag

router = APIRouter(tags=["study"])


@router.get("/study/ask")
def ask(q: str, k: int = 3) -> dict:
    return rag.answer(q, k=k)
