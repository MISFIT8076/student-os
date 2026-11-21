"""Unit and API integration tests for user authentication and dynamic app connections."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.auth import create_access_token, decode_access_token, hash_password, verify_password
from app.main import app
from app.security import TokenVault
from app.store import (
    create_user,
    delete_user_connection,
    get_user_by_email,
    get_user_by_id,
    get_user_connection,
    list_user_connections,
    upsert_user_connection,
)

client = TestClient(app)


def test_password_hashing():
    raw = "MySuperSecret123!"
    hashed = hash_password(raw)
    assert hashed != raw
    assert "$" in hashed
    assert verify_password(raw, hashed) is True
    assert verify_password("WrongPassword", hashed) is False


def test_jwt_token_creation_and_decoding():
    payload = {"sub": "42", "email": "student@university.edu"}
    token = create_access_token(payload)
    assert isinstance(token, str)

    decoded = decode_access_token(token)
    assert decoded is not None
    assert decoded["sub"] == "42"
    assert decoded["email"] == "student@university.edu"
    assert "exp" in decoded


def test_token_vault_encryption():
    vault = TokenVault()
    assert vault.available() is True
    secret = "ghp_PersonalAccessTokenABC123"
    encrypted = vault.encrypt(secret)
    assert encrypted != secret
    assert vault.decrypt(encrypted) == secret


def test_auth_registration_and_login_flow():
    import uuid
    unique_email = f"test_{uuid.uuid4().hex[:8]}@example.com"
    pwd = "SecurePassword123"

    # Register
    reg_res = client.post("/api/auth/register", json={
        "email": unique_email,
        "name": "Alex Student",
        "password": pwd,
    })
    assert reg_res.status_code == 200, reg_res.text
    data = reg_res.json()
    assert "access_token" in data
    assert data["user"]["email"] == unique_email
    assert data["user"]["name"] == "Alex Student"
    user_id = data["user"]["id"]

    # Duplicate registration should return 409 Conflict
    dup_res = client.post("/api/auth/register", json={
        "email": unique_email,
        "name": "Alex Student",
        "password": pwd,
    })
    assert dup_res.status_code == 409

    # Login with valid credentials
    login_res = client.post("/api/auth/login", json={
        "email": unique_email,
        "password": pwd,
    })
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]

    # Login with wrong password
    bad_login = client.post("/api/auth/login", json={
        "email": unique_email,
        "password": "WrongPassword!",
    })
    assert bad_login.status_code == 401

    # Protected me endpoint
    me_res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    assert me_res.json()["id"] == user_id
    assert me_res.json()["email"] == unique_email


def test_google_auth_flow():
    import uuid
    g_email = f"google_{uuid.uuid4().hex[:8]}@gmail.com"
    g_id = f"g_id_{uuid.uuid4().hex[:12]}"

    res = client.post("/api/auth/google", json={
        "email": g_email,
        "name": "Google User",
        "google_id": g_id,
        "avatar_url": "https://lh3.googleusercontent.com/photo.jpg",
    })
    assert res.status_code == 200
    data = res.json()
    assert data["user"]["email"] == g_email
    assert data["user"]["name"] == "Google User"
    token = data["access_token"]

    # Call /me with token
    me_res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    assert me_res.json()["email"] == g_email


def test_connections_endpoints():
    import uuid
    email = f"conn_user_{uuid.uuid4().hex[:8]}@univ.edu"
    reg = client.post("/api/auth/register", json={
        "email": email,
        "name": "Dev User",
        "password": "Password123!",
    })
    token = reg.json()["access_token"]
    user_id = reg.json()["user"]["id"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Get connections list
    list_res = client.get("/api/connections", headers=headers)
    assert list_res.status_code == 200
    providers = [c["provider"] for c in list_res.json()]
    assert "github" in providers
    assert "codeforces" in providers
    assert "google" in providers
    assert "gemini" in providers

    # 2. Directly test store upsert and get
    vault = TokenVault()
    encrypted = vault.encrypt('{"handle": "tourist"}')
    upsert_user_connection(user_id, "codeforces", encrypted, status="connected", meta={"rating": 3800})

    conn = get_user_connection(user_id, "codeforces")
    assert conn is not None
    assert conn["status"] == "connected"
    assert conn["meta"]["rating"] == 3800

    # 3. Check list reflects the connection
    list_res2 = client.get("/api/connections", headers=headers)
    cf_conn = next(c for c in list_res2.json() if c["provider"] == "codeforces")
    assert cf_conn["is_connected"] is True
    assert cf_conn["meta"]["rating"] == 3800

    # 4. Disconnect
    del_res = client.delete("/api/connections/codeforces", headers=headers)
    assert del_res.status_code == 200
    assert del_res.json()["disconnected"] is True

    # Confirm disconnected
    conn_after = get_user_connection(user_id, "codeforces")
    assert conn_after is None
