"""Shared Google OAuth 2.0 for the Gmail and Calendar MCP servers.

One module handles the whole token lifecycle so both servers stay tiny:

    login()            one-time browser consent -> saves a refresh token
    has_credentials()  is there a usable token on disk?
    get_credentials()  load + auto-refresh, or None
    authed_get(url)    authenticated GET against a Google REST endpoint

Run the one-time login from the backend/ directory:

    python -m mcp_servers.common.google_auth login

Google libraries are imported lazily so the servers still run in mock mode
even if these packages aren't installed yet.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

# Read-only scopes — the app never modifies the student's data.
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/classroom.courses.readonly",
    "https://www.googleapis.com/auth/classroom.coursework.me.readonly",
    "https://www.googleapis.com/auth/classroom.announcements.readonly",
    "https://www.googleapis.com/auth/classroom.student-submissions.me.readonly",
]

BACKEND_ROOT = Path(__file__).resolve().parents[2]
TOKEN_PATH = BACKEND_ROOT / ".google_token.json"


def _load_env() -> None:
    try:
        from dotenv import load_dotenv

        for p in [
            BACKEND_ROOT.parent / ".env",
            BACKEND_ROOT / ".env",
            BACKEND_ROOT.parent.parent / ".env",
        ]:
            if p.exists():
                load_dotenv(p, override=False)
    except Exception:
        pass


def _client_config() -> dict:
    import os

    _load_env()
    client_id = os.getenv("GOOGLE_CLIENT_ID", "")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET", "")
    if not client_id or not client_secret:
        raise RuntimeError(
            "GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET are not set. "
            "See docs/SETUP.md section 3."
        )
    return {
        "installed": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["http://localhost"],
        }
    }


def login() -> None:
    """Run the one-time installed-app OAuth flow and persist the token."""
    import os
    os.environ["OAUTHLIB_RELAX_TOKEN_SCOPE"] = "1"
    from google_auth_oauthlib.flow import InstalledAppFlow

    flow = InstalledAppFlow.from_client_config(_client_config(), SCOPES)
    creds = flow.run_local_server(port=0)
    TOKEN_PATH.write_text(creds.to_json())
    print(f"✅ Saved Google token to {TOKEN_PATH}")


def has_credentials() -> bool:
    return bool(os.getenv("GOOGLE_TOKEN_JSON")) or TOKEN_PATH.exists()


def get_credentials() -> Any | None:
    """Load stored credentials, refreshing them if expired. None if missing."""
    token_json_env = os.getenv("GOOGLE_TOKEN_JSON")
    if token_json_env:
        try:
            import json
            from google.auth.transport.requests import Request
            from google.oauth2.credentials import Credentials

            data = json.loads(token_json_env)
            creds = Credentials.from_authorized_user_info(data, SCOPES)
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            return creds
        except Exception as exc:
            import sys
            print(f"[google_auth] failed to load GOOGLE_TOKEN_JSON: {exc}", file=sys.stderr)

    if not TOKEN_PATH.exists():
        return None
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials

    creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        TOKEN_PATH.write_text(creds.to_json())
    return creds


def authed_get(url: str, params: dict | None = None) -> dict:
    """Authenticated GET against a Google REST endpoint. Raises if no token."""
    import httpx

    creds = get_credentials()
    if creds is None:
        raise RuntimeError("No Google credentials. Run the login command first.")
    headers = {"Authorization": f"Bearer {creds.token}"}
    with httpx.Client(timeout=20) as client:
        resp = client.get(url, params=params or {}, headers=headers)
        resp.raise_for_status()
        return resp.json()


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "login":
        login()
    else:
        print("Usage: python -m mcp_servers.common.google_auth login")
