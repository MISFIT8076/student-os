"""MCP client manager.

Reads backend/servers.json, launches each enabled MCP server as a subprocess
over stdio, lists its tools, and calls them to collect raw items. This is the
"MCP Orchestrator (Tool Router)" box in the proposal's architecture diagram.

Everything degrades gracefully: if one server fails to start or a tool errors,
that server is skipped and the rest still produce a briefing.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from app.cache import get_cache
from app.config import BACKEND_ROOT, get_settings
from app.schemas import ActionItem, Priority, ToolInfo

_CACHE_VERSION = "v2"


def _cache_key(user_id: int | None = None) -> str:
    mode = "mock" if get_settings().student_os_mock else "real"
    u = f"user_{user_id}" if user_id else "global"
    return f"student_os:{_CACHE_VERSION}:items:{u}:{mode}"


def _load_registry() -> list[dict]:
    cfg = get_settings().servers_config
    data = json.loads(Path(cfg).read_text())
    return [s for s in data.get("servers", []) if s.get("enabled", True)]


def _child_env(user_id: int | None = None) -> dict[str, str]:
    """Environment passed to each server subprocess.

    We forward the real environment (so `python` and tokens resolve) and add
    PYTHONPATH=backend/ so `python -m mcp_servers.<x>.server` imports cleanly
    regardless of the working directory.

    If user_id is provided, dynamically decrypts and injects saved user connections.
    """
    settings = get_settings()
    env = dict(os.environ)
    env["PYTHONPATH"] = str(BACKEND_ROOT) + os.pathsep + env.get("PYTHONPATH", "")
    env["STUDENT_OS_MOCK"] = "true" if settings.student_os_mock else "false"
    if settings.github_token:
        env["GITHUB_TOKEN"] = settings.github_token
    if settings.google_client_id:
        env["GOOGLE_CLIENT_ID"] = settings.google_client_id
    if settings.google_client_secret:
        env["GOOGLE_CLIENT_SECRET"] = settings.google_client_secret
    if settings.google_oauth_redirect:
        env["GOOGLE_OAUTH_REDIRECT"] = settings.google_oauth_redirect
    if settings.codeforces_handle:
        env["CODEFORCES_HANDLE"] = settings.codeforces_handle

    if user_id:
        try:
            from app.security import TokenVault
            from app.store import list_user_connections

            vault = TokenVault()
            has_connected_apps = False
            for conn in list_user_connections(user_id):
                if conn.get("status") == "connected" and conn.get("encrypted_credentials"):
                    try:
                        raw = vault.decrypt(conn["encrypted_credentials"])
                        creds = json.loads(raw)
                        prov = conn.get("provider")
                        if prov == "github" and creds.get("token"):
                            env["GITHUB_TOKEN"] = creds["token"]
                            has_connected_apps = True
                        elif prov == "codeforces" and creds.get("handle"):
                            env["CODEFORCES_HANDLE"] = creds["handle"]
                            has_connected_apps = True
                        elif prov == "gemini" and creds.get("api_key"):
                            env["GEMINI_API_KEY"] = creds["api_key"]
                        elif prov == "google" and creds:
                            google_data = dict(creds)
                            if settings.google_client_id and "client_id" not in google_data:
                                google_data["client_id"] = settings.google_client_id
                            if settings.google_client_secret and "client_secret" not in google_data:
                                google_data["client_secret"] = settings.google_client_secret
                            env["GOOGLE_TOKEN_JSON"] = json.dumps(google_data)
                            has_connected_apps = True
                    except Exception:
                        pass
            if has_connected_apps:
                env["STUDENT_OS_MOCK"] = "false"
        except Exception:
            pass

    return env


def _parse_tool_result(result: Any) -> list[dict]:
    """Normalize a CallToolResult into a list of plain dicts.

    Handles two SDK shapes:
      * newer SDKs expose `structuredContent` ({"result": [...]});
      * older SDKs (e.g. 1.2.x) return one text block PER list element, each
        block's text being the JSON of a single item — so we must decode each
        block independently rather than concatenating them.
    """
    structured = getattr(result, "structuredContent", None)
    if isinstance(structured, dict) and "result" in structured:
        structured = structured["result"]
    if isinstance(structured, list):
        return [x for x in structured if isinstance(x, dict)]

    items: list[dict] = []
    for block in getattr(result, "content", []) or []:
        text = getattr(block, "text", None)
        if not text:
            continue
        try:
            loaded = json.loads(text)
        except json.JSONDecodeError:
            continue
        if isinstance(loaded, dict):
            items.append(loaded)
        elif isinstance(loaded, list):
            items.extend(x for x in loaded if isinstance(x, dict))
    return items


def _to_action_item(server: str, raw: dict) -> ActionItem:
    return ActionItem(
        source=server,
        kind=raw.get("kind", "item"),
        title=raw.get("title", "(untitled)"),
        detail=raw.get("detail", ""),
        url=raw.get("url"),
        due=raw.get("due"),
        priority=Priority.medium,
        raw=raw.get("extra", {}),
    )


def _resolve_command(command: str) -> str:
    """Use the virtualenv interpreter if available, otherwise the running interpreter."""
    if command in ("python", "python3"):
        venv_win = BACKEND_ROOT / ".venv" / "Scripts" / "python.exe"
        if venv_win.exists():
            return str(venv_win)
        venv_nix = BACKEND_ROOT / ".venv" / "bin" / "python"
        if venv_nix.exists():
            return str(venv_nix)
        if sys.executable:
            return sys.executable
    return command


async def _collect_from_server(spec: dict, user_id: int | None = None) -> tuple[list[ActionItem], list[ToolInfo]]:
    """Launch one server, call all its tools, return normalized items + tools."""
    params = StdioServerParameters(
        command=_resolve_command(spec["command"]),
        args=spec.get("args", []),
        env=_child_env(user_id),
    )
    items: list[ActionItem] = []
    tools: list[ToolInfo] = []
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            listed = await session.list_tools()
            for tool in listed.tools:
                tools.append(
                    ToolInfo(
                        server=spec["name"],
                        name=tool.name,
                        description=tool.description or "",
                    )
                )
                try:
                    result = await session.call_tool(tool.name, {})
                    for raw in _parse_tool_result(result):
                        items.append(_to_action_item(spec["name"], raw))
                except Exception:  # noqa: BLE001 — one bad tool shouldn't kill the run
                    continue
    return items, tools


def _dedupe(items: list[ActionItem]) -> list[ActionItem]:
    """Drop duplicates that surface from more than one tool on a server."""
    seen: set[tuple[str, str, str]] = set()
    out: list[ActionItem] = []
    for it in items:
        key = (it.source, it.title.strip().lower(), it.due or "")
        if key in seen:
            continue
        seen.add(key)
        out.append(it)
    return out


async def _gather_raw(user_id: int | None = None) -> tuple[list[ActionItem], list[str], list[ToolInfo]]:
    """Internal loop over all registered servers to collect items and tools."""
    all_items: list[ActionItem] = []
    sources: list[str] = []
    all_tools: list[ToolInfo] = []
    for spec in _load_registry():
        try:
            items, tools = await _collect_from_server(spec, user_id=user_id)
            all_items.extend(items)
            all_tools.extend(tools)
            sources.append(spec["name"])
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning("ERR in _gather_raw for %s: %s: %s", spec.get('name'), type(e).__name__, e)
            continue
    return all_items, sources, all_tools


def _gather_raw_in_proactor_thread(user_id: int | None = None) -> tuple[list[ActionItem], list[str], list[ToolInfo]]:
    """Run gathering in a thread with a ProactorEventLoop (required on Windows with uvicorn)."""
    import asyncio
    import logging
    _log = logging.getLogger(__name__)
    loop = asyncio.WindowsProactorEventLoopPolicy().new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        res = loop.run_until_complete(_gather_raw(user_id=user_id))
        return res
    except Exception as e:
        _log.error("ERR in _gather_raw_in_proactor_thread: %s: %s", type(e).__name__, e)
        raise
    finally:
        loop.close()


async def gather_action_items(
    force_refresh: bool = False,
    user_id: int | None = None,
) -> tuple[list[ActionItem], list[str], list[ToolInfo], bool]:
    """Fan out across every enabled MCP server and merge their items."""
    cache = get_cache()
    key = _cache_key(user_id)

    if not force_refresh:
        hit = cache.get(key)
        if hit is not None:
            items = [ActionItem(**d) for d in hit["items"]]
            tools = [ToolInfo(**d) for d in hit["tools"]]
            return items, hit["sources"], tools, True

    import asyncio
    running_loop = asyncio.get_running_loop()
    if sys.platform == "win32" and not isinstance(running_loop, getattr(asyncio, "ProactorEventLoop", ())):
        all_items, sources, all_tools = await asyncio.to_thread(_gather_raw_in_proactor_thread, user_id)
    else:
        all_items, sources, all_tools = await _gather_raw(user_id)

    deduped = _dedupe(all_items)
    cache.set(
        key,
        {
            "items": [i.model_dump(mode="json") for i in deduped],
            "sources": sources,
            "tools": [t.model_dump() for t in all_tools],
        },
        get_settings().cache_ttl_seconds,
    )
    return deduped, sources, all_tools, False


async def list_all_tools(user_id: int | None = None) -> list[ToolInfo]:
    """Discover every tool across servers (used by the chat router)."""
    _items, _sources, tools, _cached = await gather_action_items(user_id=user_id)
    return tools
