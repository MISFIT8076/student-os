"""Kairo backend entrypoint.

Run:  uvicorn app.main:app --reload   (from the backend/ directory)
Docs: http://127.0.0.1:8000/docs
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import (
    actions,
    auth,
    briefing,
    chat,
    connections,
    feedback,
    notify,
    opportunities,
    schedule,
    study,
    tasks,
)
from app.store import _mongo_db, sync_sqlite_to_mongodb

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: safely mirror SQLite records to MongoDB Atlas if collections are fresh
    try:
        sync_sqlite_to_mongodb()
    except Exception:
        pass
    yield


app = FastAPI(
    title="Kairo",
    description="An MCP-powered, learning-based AI coordination layer for student life.",
    version="0.18.0",
    lifespan=lifespan,
)

# Allow the local Next.js dev server to call the API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(connections.router)
app.include_router(briefing.router)
app.include_router(chat.router)
app.include_router(feedback.router)
app.include_router(schedule.router)
app.include_router(notify.router)
app.include_router(opportunities.router)
app.include_router(actions.router)
app.include_router(study.router)
app.include_router(tasks.router)


@app.get("/health", tags=["meta"])
def health() -> dict:
    mdb = _mongo_db()
    return {
        "status": "ok",
        "mock_mode": settings.student_os_mock,
        "llm_enabled": settings.llm_enabled,
        "mongodb_connected": mdb is not None,
    }


@app.get("/", tags=["meta"])
def root() -> dict:
    return {
        "app": "Kairo",
        "description": "The Opportune Moment (καιρός) · AI coordination layer",
        "try": ["/briefing", "/schedule", "/opportunities", "/tools", "POST /chat", "/docs"],
    }
