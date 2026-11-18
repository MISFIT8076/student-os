"""Student OS backend entrypoint.

Run:  uvicorn app.main:app --reload   (from the backend/ directory)
Docs: http://127.0.0.1:8000/docs
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import (
    briefing,
    chat,
)

settings = get_settings()

app = FastAPI(
    title="Student OS",
    description="An MCP-powered AI coordination layer for student life.",
    version="0.2.0",
)

# Allow the local Next.js dev server to call the API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:3001", "http://127.0.0.1:3001"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(briefing.router)
app.include_router(chat.router)


@app.get("/health", tags=["meta"])
def health() -> dict:
    return {
        "status": "ok",
        "mock_mode": settings.student_os_mock,
        "llm_enabled": settings.llm_enabled,
    }


@app.get("/", tags=["meta"])
def root() -> dict:
    return {
        "app": "Student OS",
        "try": ["/briefing", "/tools", "POST /chat", "/docs"],
    }
