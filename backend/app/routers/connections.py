"""App Connections and Integrations management for Kairo.

Allows users to dynamically connect external tools (GitHub, Codeforces, Google, Gemini, Telegram)
without editing any .env file. Credentials are encrypted at rest using TokenVault (Fernet).
"""
from __future__ import annotations

import json
from typing import Any, Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, status

from app.auth import get_current_user
from app.schemas import (
    ConnectionField,
    ConnectionOut,
    ConnectionTestResult,
    ConnectionUpdateRequest,
)
from app.security import TokenVault
from app.store import (
    delete_user_connection,
    get_user_connection,
    list_user_connections,
    upsert_user_connection,
)

router = APIRouter(prefix="/api/connections", tags=["connections"])
vault = TokenVault()

# Definition of supported external services
SERVICE_CATALOG: dict[str, dict[str, Any]] = {
    "github": {
        "title": "GitHub",
        "description": "Sync pull requests, assigned issues, notifications, and repository activity.",
        "icon": "github",
        "fields": [
            ConnectionField(
                name="token",
                label="Personal Access Token (classic or fine-grained)",
                type="password",
                placeholder="ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                help_text="Requires 'repo' and 'read:user' scopes.",
            )
        ],
    },
    "codeforces": {
        "title": "Codeforces",
        "description": "Track upcoming rated rounds, contest registrations, and practice stats.",
        "icon": "codeforces",
        "fields": [
            ConnectionField(
                name="handle",
                label="Codeforces Handle / Username",
                type="text",
                placeholder="e.g. tourist, misfitorg",
                help_text="Your public user handle on codeforces.com",
            )
        ],
    },
    "google": {
        "title": "Google Workspace (Gmail, Calendar, Classroom)",
        "description": "Consolidate coursework submissions, exam events, and recruiter emails.",
        "icon": "google",
        "fields": [
            ConnectionField(
                name="token",
                label="OAuth Refresh Token / Token JSON",
                type="password",
                placeholder="Paste token or connect via Google Sign-In",
                help_text="Read-only permissions for Gmail, Calendar, and Classroom.",
            )
        ],
    },
    "gemini": {
        "title": "Google Gemini AI (LLM Provider)",
        "description": "Powers intelligent RAG reasoning, executive briefing summaries, and conversational actions.",
        "icon": "gemini",
        "fields": [
            ConnectionField(
                name="api_key",
                label="Gemini API Key",
                type="password",
                placeholder="AIzaSy...",
                help_text="Get a free API key from Google AI Studio (aistudio.google.com).",
            )
        ],
    },
    "telegram": {
        "title": "Telegram Bot Alerts",
        "description": "Receive automated daily briefings and urgent deadline alerts on your phone.",
        "icon": "telegram",
        "fields": [
            ConnectionField(
                name="bot_token",
                label="Telegram Bot Token",
                type="password",
                placeholder="123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11",
                help_text="Created via @BotFather.",
            ),
            ConnectionField(
                name="chat_id",
                label="Your Telegram Chat ID",
                type="text",
                placeholder="123456789",
                help_text="Your numerical user or group chat ID.",
            ),
        ],
    },
}


def _mask_secret(val: str) -> str:
    if not val or len(val) < 8:
        return "••••••••"
    return f"{val[:4]}••••••••{val[-4:]}"


async def _verify_credentials(provider: str, creds: dict[str, Any]) -> tuple[bool, str, dict[str, Any]]:
    """Test credentials live against the service's API."""
    if provider == "codeforces":
        handle = creds.get("handle", "").strip()
        if not handle:
            return False, "Codeforces handle is required", {}
        async with httpx.AsyncClient(timeout=8.0) as client:
            try:
                res = await client.get(f"https://codeforces.com/api/user.info?handles={handle}")
                data = res.json()
                if data.get("status") == "OK" and data.get("result"):
                    user_info = data["result"][0]
                    return True, f"Verified Codeforces handle: {handle}", {
                        "handle": user_info.get("handle"),
                        "rating": user_info.get("rating", "Unrated"),
                        "rank": user_info.get("rank", "Unranked"),
                    }
                return False, f"Codeforces handle '{handle}' not found", {}
            except Exception as e:
                return False, f"Could not reach Codeforces API: {e}", {}

    elif provider == "github":
        token = creds.get("token", "").strip()
        if not token:
            return False, "GitHub token is required", {}
        async with httpx.AsyncClient(timeout=8.0) as client:
            try:
                res = await client.get(
                    "https://api.github.com/user",
                    headers={"Authorization": f"Bearer {token}", "User-Agent": "Kairo-App"},
                )
                if res.status_code == 200:
                    data = res.json()
                    return True, f"Successfully authenticated as @{data.get('login')}", {
                        "username": data.get("login"),
                        "name": data.get("name"),
                        "avatar": data.get("avatar_url"),
                    }
                return False, f"GitHub authentication failed (HTTP {res.status_code})", {}
            except Exception as e:
                return False, f"Could not reach GitHub API: {e}", {}

    elif provider == "gemini":
        api_key = creds.get("api_key", "").strip()
        if not api_key:
            return False, "Gemini API key is required", {}
        async with httpx.AsyncClient(timeout=8.0) as client:
            try:
                res = await client.get(
                    f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
                )
                if res.status_code == 200:
                    return True, "Successfully verified Gemini API key", {"provider": "gemini"}
                return False, f"Invalid Gemini API key (HTTP {res.status_code})", {}
            except Exception as e:
                return False, f"Error contacting Gemini endpoint: {e}", {}

    elif provider == "telegram":
        bot_token = creds.get("bot_token", "").strip()
        chat_id = creds.get("chat_id", "").strip()
        if not bot_token or not chat_id:
            return False, "Both bot_token and chat_id are required", {}
        async with httpx.AsyncClient(timeout=8.0) as client:
            try:
                res = await client.get(f"https://api.telegram.org/bot{bot_token}/getMe")
                if res.status_code == 200:
                    data = res.json()
                    bot_name = data.get("result", {}).get("username", "Bot")
                    return True, f"Connected to Telegram bot @{bot_name}", {"bot_name": bot_name}
                return False, "Invalid Telegram bot token", {}
            except Exception as e:
                return False, f"Telegram API unreachable: {e}", {}

    elif provider == "google":
        token = creds.get("token", "").strip()
        if not token:
            return False, "Google token is required", {}
        return True, "Google Workspace token configured", {"provider": "google"}

    return False, f"Unknown provider '{provider}'", {}


@router.get("", response_model=list[ConnectionOut])
def get_connections(current_user: dict = Depends(get_current_user)) -> list[ConnectionOut]:
    """List all supported external app connections and their status for the current user."""
    user_id = current_user["id"]
    existing = {c["provider"]: c for c in list_user_connections(user_id)}

    out: list[ConnectionOut] = []
    for prov, cat in SERVICE_CATALOG.items():
        conn = existing.get(prov)
        is_conn = bool(conn and conn["status"] == "connected")
        status_val = conn["status"] if conn else "disconnected"
        meta = conn.get("meta", {}) if conn else {}

        out.append(
            ConnectionOut(
                provider=prov,
                title=cat["title"],
                description=cat["description"],
                icon=cat["icon"],
                is_connected=is_conn,
                status=status_val,
                meta=meta,
                updated_at=conn.get("updated_at") if conn else None,
                fields=cat["fields"],
            )
        )
    return out


@router.post("/{provider}", response_model=ConnectionTestResult)
async def save_connection(
    provider: str,
    req: ConnectionUpdateRequest,
    current_user: dict = Depends(get_current_user),
) -> Any:
    """Validate, encrypt, and store user credentials for a specific provider."""
    provider = provider.lower().strip()
    if provider not in SERVICE_CATALOG:
        raise HTTPException(status_code=404, detail=f"Unsupported provider '{provider}'")

    ok, message, test_data = await _verify_credentials(provider, req.credentials)
    if not ok:
        raise HTTPException(status_code=400, detail=message)

    # Encrypt credentials JSON with Fernet TokenVault
    plaintext_json = json.dumps(req.credentials)
    encrypted = vault.encrypt(plaintext_json)

    # Save to database
    upsert_user_connection(
        user_id=current_user["id"],
        provider=provider,
        encrypted_credentials=encrypted,
        status="connected",
        meta=test_data,
    )

    return {
        "provider": provider,
        "ok": True,
        "message": message,
        "data": test_data,
    }


@router.delete("/{provider}")
def disconnect_service(
    provider: str,
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Disconnect and purge saved credentials for a provider."""
    provider = provider.lower().strip()
    deleted = delete_user_connection(current_user["id"], provider)
    return {"provider": provider, "disconnected": deleted}


@router.post("/{provider}/test", response_model=ConnectionTestResult)
async def test_service_connection(
    provider: str,
    req: ConnectionUpdateRequest,
    current_user: dict = Depends(get_current_user),
) -> Any:
    """Test connection credentials without saving."""
    provider = provider.lower().strip()
    if provider not in SERVICE_CATALOG:
        raise HTTPException(status_code=404, detail=f"Unsupported provider '{provider}'")

    ok, message, test_data = await _verify_credentials(provider, req.credentials)
    return {
        "provider": provider,
        "ok": ok,
        "message": message,
        "data": test_data,
    }
