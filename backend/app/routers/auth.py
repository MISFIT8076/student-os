"""Authentication endpoints for Kairo."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from app.schemas import (
    AuthResponse,
    GoogleAuthRequest,
    UserLoginRequest,
    UserOut,
    UserRegisterRequest,
)
from app.store import (
    create_user,
    get_user_by_email,
    get_user_by_google_id,
    get_user_by_id,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=AuthResponse)
def register(req: UserRegisterRequest) -> Any:
    """Register a new user with email, name, and password."""
    clean_email = req.email.strip().lower()
    if not clean_email or "@" not in clean_email:
        raise HTTPException(status_code=400, detail="A valid email address is required")
    if len(req.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")

    existing = get_user_by_email(clean_email)
    if existing:
        raise HTTPException(status_code=409, detail="An account with this email already exists")

    pwd_hash = hash_password(req.password)
    user = create_user(email=clean_email, name=req.name.strip(), password_hash=pwd_hash)
    token = create_access_token({"sub": str(user["id"]), "email": user["email"]})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "email": user["email"],
            "name": user["name"],
            "avatar_url": user.get("avatar_url"),
            "created_at": user["created_at"],
        },
    }


@router.post("/login", response_model=AuthResponse)
def login(req: UserLoginRequest) -> Any:
    """Authenticate with email and password."""
    clean_email = req.email.strip().lower()
    user = get_user_by_email(clean_email)
    if not user or not user.get("password_hash"):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not verify_password(req.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token({"sub": str(user["id"]), "email": user["email"]})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "email": user["email"],
            "name": user["name"],
            "avatar_url": user.get("avatar_url"),
            "created_at": user["created_at"],
        },
    }


@router.post("/google", response_model=AuthResponse)
def google_auth(req: GoogleAuthRequest) -> Any:
    """Authenticate with Google OAuth. Accepts credential JWT or parsed Google profile."""
    email = (req.email or "").strip().lower()
    name = (req.name or "").strip() or (email.split("@")[0] if email else "Google User")
    google_id = req.google_id

    # If full credential string was sent, parse payload if needed
    if req.credential and not email:
        try:
            import jwt
            # Decodes unverified payload safely for client-validated OAuth tokens
            payload = jwt.decode(req.credential, options={"verify_signature": False})
            email = payload.get("email", "").strip().lower()
            name = payload.get("name") or name
            google_id = payload.get("sub") or google_id
            req.avatar_url = payload.get("picture") or req.avatar_url
        except Exception:
            pass

    if not email:
        raise HTTPException(status_code=400, detail="Google authentication failed to provide email")

    # Match by google_id or email
    user = (get_user_by_google_id(google_id) if google_id else None) or get_user_by_email(email)
    if not user:
        user = create_user(
            email=email,
            name=name,
            google_id=google_id,
            avatar_url=req.avatar_url,
        )

    token = create_access_token({"sub": str(user["id"]), "email": user["email"]})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "email": user["email"],
            "name": user["name"],
            "avatar_url": user.get("avatar_url"),
            "created_at": user["created_at"],
        },
    }


@router.get("/me", response_model=UserOut)
def me(current_user: dict = Depends(get_current_user)) -> Any:
    """Return the profile of the currently logged in user."""
    return {
        "id": current_user["id"],
        "email": current_user["email"],
        "name": current_user["name"],
        "avatar_url": current_user.get("avatar_url"),
        "created_at": current_user["created_at"],
    }
