"""GitHub MCP server.

Exposes read-only tools describing what needs the student's attention on
GitHub: open pull requests they authored, issues assigned to them, and
unread notifications.

Runs in two modes:
  * REAL  — when GITHUB_TOKEN is set or user is connected, it calls
            the GitHub REST API (https://api.github.com).
  * MOCK  — otherwise it returns realistic sample data so the whole system
            works with zero setup.
"""
from __future__ import annotations

import os
from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP

from mcp_servers.common.util import mock_enabled

mcp = FastMCP("github")

GITHUB_API = "https://api.github.com"


# ── helpers ────────────────────────────────────────────────────────────────
def _token() -> str:
    return os.getenv("GITHUB_TOKEN", "")


def _use_real() -> bool:
    if bool(_token()):
        return True
    return not mock_enabled()


def _get(path: str, params: dict[str, Any] | None = None) -> Any:
    """Authenticated GET against the GitHub API. Raises on HTTP error."""
    headers = {
        "Authorization": f"Bearer {_token()}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    with httpx.Client(base_url=GITHUB_API, headers=headers, timeout=15) as client:
        resp = client.get(path, params=params or {})
        resp.raise_for_status()
        return resp.json()


def _login() -> str:
    return _get("/user")["login"]


# ── tools ──────────────────────────────────────────────────────────────────
@mcp.tool()
def list_open_pull_requests() -> list[dict]:
    """List open pull requests authored by the student across all repos."""
    if not _use_real():
        return _MOCK_PRS
    try:
        login = _login()
        data = _get(
            "/search/issues",
            {"q": f"is:open is:pr author:{login}", "per_page": 20},
        )
        return [
            {
                "kind": "pull_request",
                "title": it["title"],
                "detail": f"{it['repository_url'].split('/')[-1]} #{it['number']}"
                + (" · review requested" if it.get("draft") is False else ""),
                "url": it["html_url"],
                "due": None,
                "extra": {"comments": it.get("comments", 0)},
            }
            for it in data.get("items", [])
        ]
    except Exception as exc:  # noqa: BLE001
        if _use_real():
            return [_error_item("list_open_pull_requests", exc)]
        return [_error_item("list_open_pull_requests", exc)] + _MOCK_PRS


@mcp.tool()
def list_assigned_issues() -> list[dict]:
    """List open issues assigned to the student."""
    if not _use_real():
        return _MOCK_ISSUES
    try:
        login = _login()
        data = _get(
            "/search/issues",
            {"q": f"is:open is:issue assignee:{login}", "per_page": 20},
        )
        return [
            {
                "kind": "issue",
                "title": it["title"],
                "detail": f"{it['repository_url'].split('/')[-1]} #{it['number']}",
                "url": it["html_url"],
                "due": None,
                "extra": {"labels": [l["name"] for l in it.get("labels", [])]},
            }
            for it in data.get("items", [])
        ]
    except Exception as exc:  # noqa: BLE001
        if _use_real():
            return [_error_item("list_assigned_issues", exc)]
        return [_error_item("list_assigned_issues", exc)] + _MOCK_ISSUES


@mcp.tool()
def list_notifications() -> list[dict]:
    """List the student's unread GitHub notifications."""
    if not _use_real():
        return _MOCK_NOTIFS
    try:
        data = _get("/notifications", {"per_page": 20})
        return [
            {
                "kind": "notification",
                "title": n["subject"]["title"],
                "detail": f"{n['repository']['full_name']} · {n['reason']}",
                "url": (n["subject"].get("url") or "").replace(
                    "api.github.com/repos", "github.com"
                ),
                "due": None,
                "extra": {"type": n["subject"]["type"]},
            }
            for n in data
        ]
    except Exception as exc:  # noqa: BLE001
        if _use_real():
            return [_error_item("list_notifications", exc)]
        return [_error_item("list_notifications", exc)] + _MOCK_NOTIFS


@mcp.tool()
def list_recent_repositories() -> list[dict]:
    """List recently updated repositories for the student."""
    if not _use_real():
        return []
    try:
        repos = _get(
            "/user/repos",
            {"sort": "updated", "per_page": 5, "affiliation": "owner,collaborator"},
        )
        return [
            {
                "kind": "repository",
                "title": f"Repository: {r['name']}",
                "detail": f"{r.get('description') or 'Active GitHub repo'} · Updated {r.get('updated_at', '')[:10]}",
                "url": r.get("html_url"),
                "due": None,
                "extra": {
                    "stars": r.get("stargazers_count", 0),
                    "forks": r.get("forks_count", 0),
                    "private": r.get("private", False),
                },
            }
            for r in repos
        ]
    except Exception:
        return []


def _error_item(tool: str, exc: Exception) -> dict:
    return {
        "kind": "error",
        "title": f"GitHub API error in {tool}",
        "detail": f"{type(exc).__name__}: {exc}.",
        "url": None,
        "due": None,
        "extra": {},
    }


# ── mock data ────────────────────────────────────────────────────────────
_MOCK_PRS = [
    {
        "kind": "pull_request",
        "title": "Add MCP orchestrator tool router",
        "detail": "student-os #14 · review requested",
        "url": "https://github.com/example/student-os/pull/14",
        "due": None,
        "extra": {"comments": 3},
    },
]

_MOCK_ISSUES = [
    {
        "kind": "issue",
        "title": "Implement token refresh loop for Google OAuth",
        "detail": "student-os #9",
        "url": "https://github.com/example/student-os/issues/9",
        "due": None,
        "extra": {"labels": ["enhancement", "auth"]},
    },
]

_MOCK_NOTIFS = [
    {
        "kind": "notification",
        "title": "Reviewed PR #12: Fix caching in memory store",
        "detail": "example/student-os · mention",
        "url": "https://github.com/example/student-os/pull/12",
        "due": None,
        "extra": {"type": "PullRequest"},
    },
]

if __name__ == '__main__':
    mcp.run()

