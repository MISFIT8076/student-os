"""Persistence layer — the memory that makes learning and progress possible.

Uses SQLAlchemy Core so one code path works for both:
  * SQLite (default, zero setup) — a file at backend/student_os.db;
  * PostgreSQL — set DATABASE_URL=postgresql+psycopg://user:pass@host/db.

Two tables:
  * shown_items — every action item we surfaced in a briefing (+ its features);
  * feedback    — what the student did about an item (opened/done/dismissed/snoozed).

Together these are the raw material for the learned ranker (labels), the
progress dashboard (stats), and any future analytics. All writes are
best-effort: a storage hiccup must never break a briefing.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from functools import lru_cache

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    create_engine,
    delete,
    func,
    insert,
    select,
)

from app.config import get_settings

_metadata = MetaData()

shown_items = Table(
    "shown_items",
    _metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("ts", DateTime, nullable=False),
    Column("briefing_ts", String(40), nullable=False),
    Column("item_key", String(64), nullable=False, index=True),
    Column("source", String(40), nullable=False),
    Column("kind", String(40), nullable=False),
    Column("title", Text, nullable=False),
    Column("due", String(40)),
    Column("rank_position", Integer, nullable=False),
    Column("score", Float, nullable=False),
    Column("priority", String(16), nullable=False),
    Column("ranker", String(16), nullable=False),
    Column("features", Text),  # JSON
)

feedback = Table(
    "feedback",
    _metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("ts", DateTime, nullable=False),
    Column("item_key", String(64), nullable=False, index=True),
    Column("source", String(40), nullable=False),
    Column("kind", String(40), nullable=False),
    Column("title", Text, nullable=False),
    Column("action", String(16), nullable=False),  # opened|done|dismissed|snoozed
)

opportunity_status = Table(
    "opportunity_status",
    _metadata,
    Column("item_key", String(64), primary_key=True),
    Column("source", String(40), nullable=False),
    Column("title", Text, nullable=False),
    Column("due", String(40)),
    Column("kind", String(40)),
    Column("otype", String(24)),
    Column("status", String(24), nullable=False),
    Column("updated_at", DateTime, nullable=False),
)

users = Table(
    "users",
    _metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("email", String(255), unique=True, nullable=False, index=True),
    Column("name", String(255), nullable=False),
    Column("password_hash", String(255), nullable=True),
    Column("google_id", String(255), nullable=True, index=True),
    Column("avatar_url", String(512), nullable=True),
    Column("created_at", DateTime, nullable=False),
)

user_connections = Table(
    "user_connections",
    _metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("user_id", Integer, nullable=False, index=True),
    Column("provider", String(50), nullable=False, index=True),
    Column("encrypted_credentials", Text, nullable=False),
    Column("status", String(24), nullable=False),
    Column("meta", Text, nullable=True),
    Column("updated_at", DateTime, nullable=False),
)

VALID_ACTIONS = {"opened", "done", "dismissed", "snoozed"}
VALID_OPP_STATUS = {"new", "interested", "applied", "rejected", "offer", "closed"}


def item_key(source: str, title: str, due: str | None) -> str:
    """Stable id for 'the same item' across briefings."""
    raw = f"{source}|{title.strip().lower()}|{due or ''}"
    return hashlib.sha1(raw.encode()).hexdigest()[:16]


@lru_cache
def _engine():
    eng = create_engine(get_settings().resolved_database_url, future=True)
    _metadata.create_all(eng)  # idempotent
    return eng


def _now() -> datetime:
    return datetime.now(timezone.utc)


def record_briefing(items: list, ranker: str, features_by_key: dict | None = None) -> bool:
    """Log the items shown in one briefing. Best-effort; returns success."""
    if not get_settings().persist_enabled:
        return False
    features_by_key = features_by_key or {}
    stamp = _now()
    briefing_ts = stamp.isoformat(timespec="seconds")
    rows = []
    for pos, it in enumerate(items, start=1):
        key = item_key(it.source, it.title, it.due)
        rows.append(
            {
                "ts": stamp,
                "briefing_ts": briefing_ts,
                "item_key": key,
                "source": it.source,
                "kind": it.kind,
                "title": it.title,
                "due": it.due,
                "rank_position": pos,
                "score": float(it.score),
                "priority": it.priority.value if hasattr(it.priority, "value") else str(it.priority),
                "ranker": ranker,
                "features": json.dumps(features_by_key.get(key, {})),
            }
        )
    try:
        with _engine().begin() as conn:
            conn.execute(insert(shown_items), rows)
        return True
    except Exception:  # noqa: BLE001 — never break a briefing over logging
        return False


def record_feedback(source: str, kind: str, title: str, due: str | None, action: str) -> bool:
    """Log a student action on an item."""
    if action not in VALID_ACTIONS:
        raise ValueError(f"action must be one of {sorted(VALID_ACTIONS)}")
    try:
        with _engine().begin() as conn:
            conn.execute(
                insert(feedback),
                [{
                    "ts": _now(),
                    "item_key": item_key(source, title, due),
                    "source": source,
                    "kind": kind,
                    "title": title,
                    "action": action,
                }],
            )
        return True
    except Exception:  # noqa: BLE001
        return False


def set_opportunity_status(source: str, title: str, due: str | None, kind: str,
                           otype: str, status: str) -> bool:
    """Upsert the application status for one opportunity."""
    if status not in VALID_OPP_STATUS:
        raise ValueError(f"status must be one of {sorted(VALID_OPP_STATUS)}")
    key = item_key(source, title, due)
    try:
        with _engine().begin() as conn:
            conn.execute(delete(opportunity_status).where(opportunity_status.c.item_key == key))
            conn.execute(insert(opportunity_status), [{
                "item_key": key, "source": source, "title": title, "due": due,
                "kind": kind, "otype": otype, "status": status, "updated_at": _now(),
            }])
        return True
    except Exception:  # noqa: BLE001
        return False


def get_opportunity_statuses() -> dict[str, str]:
    """Map item_key -> status for all tracked opportunities."""
    try:
        with _engine().begin() as conn:
            rows = conn.execute(
                select(opportunity_status.c.item_key, opportunity_status.c.status)
            ).all()
        return {k: v for k, v in rows}
    except Exception:  # noqa: BLE001
        return {}


def get_progress() -> dict:
    """Aggregates for the progress/habit dashboard: streak, actions, funnel."""
    from datetime import date, timedelta

    try:
        with _engine().begin() as conn:
            actions = dict(conn.execute(
                select(feedback.c.action, func.count()).group_by(feedback.c.action)
            ).all())
            done_rows = conn.execute(
                select(feedback.c.ts).where(feedback.c.action == "done")
            ).all()
            funnel = dict(conn.execute(
                select(opportunity_status.c.status, func.count())
                .group_by(opportunity_status.c.status)
            ).all())
            shown = conn.execute(select(func.count()).select_from(shown_items)).scalar() or 0

        # "Done" streak: consecutive days up to today with at least one completion.
        # Timestamps are stored in UTC, so compare against the UTC date to match.
        done_dates = set()
        for (ts,) in done_rows:
            done_dates.add(ts.date() if hasattr(ts, "date") else date.fromisoformat(str(ts)[:10]))
        streak, cursor = 0, datetime.now(timezone.utc).date()
        while cursor in done_dates:
            streak += 1
            cursor -= timedelta(days=1)

        return {
            "items_shown": shown,
            "actions": actions,
            "total_actions": sum(actions.values()),
            "done_streak_days": streak,
            "active_days": len(done_dates),
            "application_funnel": funnel,
        }
    except Exception:  # noqa: BLE001
        return {"items_shown": 0, "actions": {}, "total_actions": 0,
                "done_streak_days": 0, "active_days": 0, "application_funnel": {}}


def get_stats() -> dict:
    """Aggregate counts for the progress dashboard."""
    try:
        with _engine().begin() as conn:
            shown = conn.execute(select(func.count()).select_from(shown_items)).scalar() or 0
            fb_total = conn.execute(select(func.count()).select_from(feedback)).scalar() or 0
            by_action = dict(
                conn.execute(
                    select(feedback.c.action, func.count()).group_by(feedback.c.action)
                ).all()
            )
            by_source = dict(
                conn.execute(
                    select(feedback.c.source, func.count()).group_by(feedback.c.source)
                ).all()
            )
        return {
            "items_shown": shown,
            "feedback_total": fb_total,
            "feedback_by_action": by_action,
            "feedback_by_source": by_source,
        }
    except Exception:  # noqa: BLE001
        return {"items_shown": 0, "feedback_total": 0, "feedback_by_action": {}, "feedback_by_source": {}}


# ── User & Connection Repository (Ready for MongoDB swap) ────────────────────
def create_user(
    email: str,
    name: str,
    password_hash: str | None = None,
    google_id: str | None = None,
    avatar_url: str | None = None,
) -> dict:
    ts = datetime.now(timezone.utc)
    with _engine().begin() as conn:
        res = conn.execute(
            insert(users).values(
                email=email.strip().lower(),
                name=name.strip(),
                password_hash=password_hash,
                google_id=google_id,
                avatar_url=avatar_url,
                created_at=ts,
            )
        )
        uid = res.inserted_primary_key[0]
    return {
        "id": uid,
        "email": email.strip().lower(),
        "name": name.strip(),
        "password_hash": password_hash,
        "google_id": google_id,
        "avatar_url": avatar_url,
        "created_at": ts.isoformat(),
    }


def get_user_by_email(email: str) -> dict | None:
    with _engine().begin() as conn:
        row = conn.execute(
            select(users).where(users.c.email == email.strip().lower())
        ).mappings().first()
        if not row:
            return None
        d = dict(row)
        d["created_at"] = (
            d["created_at"].isoformat()
            if hasattr(d["created_at"], "isoformat")
            else str(d["created_at"])
        )
        return d


def get_user_by_id(user_id: int) -> dict | None:
    with _engine().begin() as conn:
        row = conn.execute(
            select(users).where(users.c.id == user_id)
        ).mappings().first()
        if not row:
            return None
        d = dict(row)
        d["created_at"] = (
            d["created_at"].isoformat()
            if hasattr(d["created_at"], "isoformat")
            else str(d["created_at"])
        )
        return d


def get_user_by_google_id(google_id: str) -> dict | None:
    with _engine().begin() as conn:
        row = conn.execute(
            select(users).where(users.c.google_id == google_id)
        ).mappings().first()
        if not row:
            return None
        d = dict(row)
        d["created_at"] = (
            d["created_at"].isoformat()
            if hasattr(d["created_at"], "isoformat")
            else str(d["created_at"])
        )
        return d


def list_user_connections(user_id: int) -> list[dict]:
    with _engine().begin() as conn:
        rows = conn.execute(
            select(user_connections).where(user_connections.c.user_id == user_id)
        ).mappings().all()
        out = []
        for r in rows:
            d = dict(r)
            d["updated_at"] = (
                d["updated_at"].isoformat()
                if hasattr(d["updated_at"], "isoformat")
                else str(d["updated_at"])
            )
            if d.get("meta") and isinstance(d["meta"], str):
                try:
                    d["meta"] = json.loads(d["meta"])
                except Exception:
                    d["meta"] = {}
            else:
                d["meta"] = d.get("meta") or {}
            out.append(d)
        return out


def get_user_connection(user_id: int, provider: str) -> dict | None:
    with _engine().begin() as conn:
        row = conn.execute(
            select(user_connections).where(
                (user_connections.c.user_id == user_id)
                & (user_connections.c.provider == provider)
            )
        ).mappings().first()
        if not row:
            return None
        d = dict(row)
        d["updated_at"] = (
            d["updated_at"].isoformat()
            if hasattr(d["updated_at"], "isoformat")
            else str(d["updated_at"])
        )
        if d.get("meta") and isinstance(d["meta"], str):
            try:
                d["meta"] = json.loads(d["meta"])
            except Exception:
                d["meta"] = {}
        else:
            d["meta"] = d.get("meta") or {}
        return d


def upsert_user_connection(
    user_id: int,
    provider: str,
    encrypted_credentials: str,
    status: str = "connected",
    meta: dict | None = None,
) -> None:
    ts = datetime.now(timezone.utc)
    meta_json = json.dumps(meta or {})
    with _engine().begin() as conn:
        existing = conn.execute(
            select(user_connections.c.id).where(
                (user_connections.c.user_id == user_id)
                & (user_connections.c.provider == provider)
            )
        ).scalar()
        if existing:
            conn.execute(
                user_connections.update()
                .where(user_connections.c.id == existing)
                .values(
                    encrypted_credentials=encrypted_credentials,
                    status=status,
                    meta=meta_json,
                    updated_at=ts,
                )
            )
        else:
            conn.execute(
                insert(user_connections).values(
                    user_id=user_id,
                    provider=provider,
                    encrypted_credentials=encrypted_credentials,
                    status=status,
                    meta=meta_json,
                    updated_at=ts,
                )
            )


def delete_user_connection(user_id: int, provider: str) -> bool:
    with _engine().begin() as conn:
        res = conn.execute(
            delete(user_connections).where(
                (user_connections.c.user_id == user_id)
                & (user_connections.c.provider == provider)
            )
        )
        return res.rowcount > 0

