"""Shared pydantic models used across the API and orchestrator."""
from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class Priority(str, Enum):
    urgent = "urgent"
    high = "high"
    medium = "medium"
    low = "low"


class ActionItem(BaseModel):
    """A single normalized thing the student could act on.

    Every MCP server maps its native objects (a PR, an email, an event)
    into this common shape so the prioritizer can rank across sources.
    """

    source: str = Field(..., description="Originating MCP server, e.g. 'github'.")
    kind: str = Field(..., description="Type within the source, e.g. 'pull_request'.")
    title: str
    detail: str = ""
    url: Optional[str] = None
    due: Optional[str] = Field(
        None, description="ISO date/datetime if the item has a deadline."
    )
    priority: Priority = Priority.medium
    score: float = 0.0
    raw: dict[str, Any] = Field(default_factory=dict)


class Briefing(BaseModel):
    """The 'What should I do today?' response."""

    generated_at: str
    headline: str
    summary: str
    items: list[ActionItem]
    sources_used: list[str]
    llm_used: bool
    cached: bool = False


class ChatRequest(BaseModel):
    message: str
    history: list[dict[str, str]] = Field(default_factory=list)


class ChatResponse(BaseModel):
    reply: str
    tool_calls: list[dict[str, Any]] = Field(default_factory=list)
    llm_used: bool


class ToolInfo(BaseModel):
    server: str
    name: str
    description: str


class FeedbackRequest(BaseModel):
    """A student action on an item — the signal the ranker learns from."""

    source: str
    kind: str
    title: str
    due: Optional[str] = None
    action: str = Field(..., description="opened | done | dismissed | snoozed")


class OpportunityStatusRequest(BaseModel):
    """Update the application status of a tracked opportunity."""

    source: str
    kind: str
    title: str
    due: Optional[str] = None
    otype: str = Field(..., description="internship | scholarship | hackathon | contest")
    status: str = Field(..., description="new | interested | applied | rejected | offer | closed")


class ProposeActionRequest(BaseModel):
    """Ask the agent to prepare an action (nothing happens until confirmed)."""

    action: str = Field(..., description="draft_reply | add_event | snooze | mark_done")
    source: str
    kind: str
    title: str
    due: Optional[str] = None


class ConfirmActionRequest(BaseModel):
    token: str


# ── Auth & Connection Schemas ───────────────────────────────────────────────
class UserRegisterRequest(BaseModel):
    email: str
    name: str
    password: str = Field(..., min_length=6)


class UserLoginRequest(BaseModel):
    email: str
    password: str


class GoogleAuthRequest(BaseModel):
    credential: Optional[str] = None
    email: Optional[str] = None
    name: Optional[str] = None
    google_id: Optional[str] = None
    avatar_url: Optional[str] = None


class UserOut(BaseModel):
    id: int
    email: str
    name: str
    avatar_url: Optional[str] = None
    created_at: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class ConnectionField(BaseModel):
    name: str
    label: str
    type: str  # text, password, select
    placeholder: str = ""
    required: bool = True
    help_text: str = ""


class ConnectionOut(BaseModel):
    provider: str
    title: str
    description: str
    icon: str
    is_connected: bool
    status: str  # connected, disconnected, error
    meta: dict[str, Any] = Field(default_factory=dict)
    updated_at: Optional[str] = None
    fields: list[ConnectionField] = Field(default_factory=list)


class ConnectionUpdateRequest(BaseModel):
    credentials: dict[str, Any]


class ConnectionTestResult(BaseModel):
    provider: str
    ok: bool
    message: str
    data: Optional[dict[str, Any]] = None

