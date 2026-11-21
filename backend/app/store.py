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
    update,
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

custom_tasks = Table(
    "custom_tasks",
    _metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("item_key", String(64), nullable=False, unique=True, index=True),
    Column("source", String(40), nullable=False, default="personal"),
    Column("kind", String(40), nullable=False, default="task"),
    Column("title", Text, nullable=False),
    Column("detail", Text, nullable=False, default=""),
    Column("due", String(40)),
    Column("priority", String(16), nullable=False, default="medium"),
    Column("created_at", DateTime, nullable=False),
    Column("is_done", Integer, nullable=False, default=0),
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


@lru_cache
def _mongo_db():
    """Return a pymongo Database instance if MONGODB_URI is configured and reachable."""
    settings = get_settings()
    if not settings.mongodb_uri:
        return None
    try:
        from pymongo import MongoClient
        client = MongoClient(settings.mongodb_uri, serverSelectionTimeoutMS=3000)
        client.admin.command("ping")
        return client[settings.mongodb_db_name or "student_os"]
    except Exception:
        return None


def sync_sqlite_to_mongodb() -> dict:
    """Safely mirror local SQLite records into MongoDB Atlas if collections are empty."""
    mdb = _mongo_db()
    if mdb is None:
        return {"status": "skipped", "reason": "mongodb_not_configured"}

    synced = {}
    try:
        with _engine().begin() as conn:
            # Sync shown_items
            if mdb["shown_items"].count_documents({}) == 0:
                rows = [dict(r) for r in conn.execute(select(shown_items)).mappings().all()]
                for r in rows:
                    r.pop("id", None)
                    r["ts"] = r["ts"].isoformat() if hasattr(r["ts"], "isoformat") else str(r["ts"])
                if rows:
                    mdb["shown_items"].insert_many(rows, ordered=False)
                synced["shown_items"] = len(rows)

            # Sync feedback
            if mdb["feedback"].count_documents({}) == 0:
                rows = [dict(r) for r in conn.execute(select(feedback)).mappings().all()]
                for r in rows:
                    r.pop("id", None)
                    r["ts"] = r["ts"].isoformat() if hasattr(r["ts"], "isoformat") else str(r["ts"])
                if rows:
                    mdb["feedback"].insert_many(rows, ordered=False)
                synced["feedback"] = len(rows)

            # Sync opportunity_status
            if mdb["opportunity_status"].count_documents({}) == 0:
                rows = [dict(r) for r in conn.execute(select(opportunity_status)).mappings().all()]
                for r in rows:
                    r["updated_at"] = r["updated_at"].isoformat() if hasattr(r["updated_at"], "isoformat") else str(r["updated_at"])
                if rows:
                    mdb["opportunity_status"].insert_many(rows, ordered=False)
                synced["opportunity_status"] = len(rows)

            # Sync users
            if mdb["users"].count_documents({}) == 0:
                rows = [dict(r) for r in conn.execute(select(users)).mappings().all()]
                for r in rows:
                    r["created_at"] = r["created_at"].isoformat() if hasattr(r["created_at"], "isoformat") else str(r["created_at"])
                if rows:
                    mdb["users"].insert_many(rows, ordered=False)
                synced["users"] = len(rows)

            # Sync user_connections
            if mdb["user_connections"].count_documents({}) == 0:
                rows = [dict(r) for r in conn.execute(select(user_connections)).mappings().all()]
                for r in rows:
                    r["updated_at"] = r["updated_at"].isoformat() if hasattr(r["updated_at"], "isoformat") else str(r["updated_at"])
                if rows:
                    mdb["user_connections"].insert_many(rows, ordered=False)
                synced["user_connections"] = len(rows)

            # Sync custom_tasks
            if mdb["custom_tasks"].count_documents({}) == 0:
                rows = [dict(r) for r in conn.execute(select(custom_tasks)).mappings().all()]
                for r in rows:
                    r.pop("id", None)
                    r["created_at"] = r["created_at"].isoformat() if hasattr(r["created_at"], "isoformat") else str(r["created_at"])
                if rows:
                    mdb["custom_tasks"].insert_many(rows, ordered=False)
                synced["custom_tasks"] = len(rows)

        return {"status": "ok", "synced": synced}
    except Exception as exc:
        return {"status": "error", "reason": str(exc)}


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
    mongo_docs = []
    for pos, it in enumerate(items, start=1):
        key = item_key(it.source, it.title, it.due)
        feat_json = json.dumps(features_by_key.get(key, {}))
        priority_val = it.priority.value if hasattr(it.priority, "value") else str(it.priority)
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
                "priority": priority_val,
                "ranker": ranker,
                "features": feat_json,
            }
        )
        mongo_docs.append(
            {
                "ts": stamp.isoformat(),
                "briefing_ts": briefing_ts,
                "item_key": key,
                "source": it.source,
                "kind": it.kind,
                "title": it.title,
                "due": it.due,
                "rank_position": pos,
                "score": float(it.score),
                "priority": priority_val,
                "ranker": ranker,
                "features": feat_json,
            }
        )
    try:
        mdb = _mongo_db()
        if mdb is not None and mongo_docs:
            mdb["shown_items"].insert_many(mongo_docs, ordered=False)
    except Exception:
        pass

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
    now = _now()
    key = item_key(source, title, due)
    try:
        mdb = _mongo_db()
        if mdb is not None:
            mdb["feedback"].insert_one({
                "ts": now.isoformat(),
                "item_key": key,
                "source": source,
                "kind": kind,
                "title": title,
                "action": action,
            })
    except Exception:
        pass

    try:
        with _engine().begin() as conn:
            conn.execute(
                insert(feedback),
                [{
                    "ts": now,
                    "item_key": key,
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
    now = _now()
    try:
        mdb = _mongo_db()
        if mdb is not None:
            mdb["opportunity_status"].replace_one(
                {"item_key": key},
                {
                    "item_key": key,
                    "source": source,
                    "title": title,
                    "due": due,
                    "kind": kind,
                    "otype": otype,
                    "status": status,
                    "updated_at": now.isoformat(),
                },
                upsert=True,
            )
    except Exception:
        pass

    try:
        with _engine().begin() as conn:
            conn.execute(delete(opportunity_status).where(opportunity_status.c.item_key == key))
            conn.execute(insert(opportunity_status), [{
                "item_key": key, "source": source, "title": title, "due": due,
                "kind": kind, "otype": otype, "status": status, "updated_at": now,
            }])
        return True
    except Exception:  # noqa: BLE001
        return False


def get_opportunity_statuses() -> dict[str, str]:
    """Map item_key -> status for all tracked opportunities."""
    try:
        mdb = _mongo_db()
        if mdb is not None:
            docs = mdb["opportunity_status"].find({}, {"item_key": 1, "status": 1, "_id": 0})
            res = {d["item_key"]: d["status"] for d in docs if "item_key" in d and "status" in d}
            if res:
                return res
    except Exception:
        pass

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


# ── User & Connection Repository (MongoDB Atlas with SQLite Fallback) ──────
def create_user(
    email: str,
    name: str,
    password_hash: str | None = None,
    google_id: str | None = None,
    avatar_url: str | None = None,
) -> dict:
    ts = datetime.now(timezone.utc)
    email_clean = email.strip().lower()
    name_clean = name.strip()

    with _engine().begin() as conn:
        res = conn.execute(
            insert(users).values(
                email=email_clean,
                name=name_clean,
                password_hash=password_hash,
                google_id=google_id,
                avatar_url=avatar_url,
                created_at=ts,
            )
        )
        uid = res.inserted_primary_key[0]

    user_dict = {
        "id": uid,
        "email": email_clean,
        "name": name_clean,
        "password_hash": password_hash,
        "google_id": google_id,
        "avatar_url": avatar_url,
        "created_at": ts.isoformat(),
    }

    try:
        mdb = _mongo_db()
        if mdb is not None:
            mdb["users"].replace_one(
                {"email": email_clean},
                user_dict,
                upsert=True,
            )
    except Exception:
        pass

    return user_dict


def get_user_by_email(email: str) -> dict | None:
    email_clean = email.strip().lower()
    try:
        mdb = _mongo_db()
        if mdb is not None:
            doc = mdb["users"].find_one({"email": email_clean}, {"_id": 0})
            if doc:
                return doc
    except Exception:
        pass

    with _engine().begin() as conn:
        row = conn.execute(
            select(users).where(users.c.email == email_clean)
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
    try:
        mdb = _mongo_db()
        if mdb is not None:
            doc = mdb["users"].find_one({"id": user_id}, {"_id": 0})
            if doc:
                return doc
    except Exception:
        pass

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
    try:
        mdb = _mongo_db()
        if mdb is not None:
            doc = mdb["users"].find_one({"google_id": google_id}, {"_id": 0})
            if doc:
                return doc
    except Exception:
        pass

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
    try:
        mdb = _mongo_db()
        if mdb is not None:
            docs = list(mdb["user_connections"].find({"user_id": user_id}, {"_id": 0}))
            if docs:
                for d in docs:
                    if not isinstance(d.get("meta"), dict):
                        d["meta"] = {}
                return docs
    except Exception:
        pass

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
    try:
        mdb = _mongo_db()
        if mdb is not None:
            doc = mdb["user_connections"].find_one(
                {"user_id": user_id, "provider": provider},
                {"_id": 0}
            )
            if doc:
                if not isinstance(doc.get("meta"), dict):
                    doc["meta"] = {}
                return doc
    except Exception:
        pass

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
    meta_dict = meta or {}
    meta_json = json.dumps(meta_dict)

    try:
        mdb = _mongo_db()
        if mdb is not None:
            mdb["user_connections"].replace_one(
                {"user_id": user_id, "provider": provider},
                {
                    "user_id": user_id,
                    "provider": provider,
                    "encrypted_credentials": encrypted_credentials,
                    "status": status,
                    "meta": meta_dict,
                    "updated_at": ts.isoformat(),
                },
                upsert=True,
            )
    except Exception:
        pass

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
    try:
        mdb = _mongo_db()
        if mdb is not None:
            mdb["user_connections"].delete_one({"user_id": user_id, "provider": provider})
    except Exception:
        pass

    with _engine().begin() as conn:
        res = conn.execute(
            delete(user_connections).where(
                (user_connections.c.user_id == user_id)
                & (user_connections.c.provider == provider)
            )
        )
        return res.rowcount > 0


def create_custom_task(title: str, detail: str = "", due: str | None = None,
                       priority: str = "medium", kind: str = "task",
                       source: str = "personal") -> dict:
    """Create and persist a custom user-defined action item."""
    key = item_key(source, title, due)
    now = _now()
    row = {
        "item_key": key,
        "source": source,
        "kind": kind,
        "title": title.strip(),
        "detail": detail.strip(),
        "due": due,
        "priority": priority,
        "created_at": now,
        "is_done": 0,
    }

    try:
        mdb = _mongo_db()
        if mdb is not None:
            mongo_doc = dict(row)
            mongo_doc["created_at"] = now.isoformat()
            mdb["custom_tasks"].replace_one(
                {"item_key": key},
                mongo_doc,
                upsert=True,
            )
    except Exception:
        pass

    with _engine().begin() as conn:
        conn.execute(delete(custom_tasks).where(custom_tasks.c.item_key == key))
        conn.execute(insert(custom_tasks), [row])
    return {
        "item_key": key,
        "source": source,
        "kind": kind,
        "title": title.strip(),
        "detail": detail.strip(),
        "due": due,
        "priority": priority,
    }


def get_active_custom_tasks() -> list[dict]:
    """Return all unfinished user-defined tasks."""
    try:
        mdb = _mongo_db()
        if mdb is not None:
            docs = list(mdb["custom_tasks"].find(
                {"is_done": 0},
                {"_id": 0, "item_key": 1, "source": 1, "kind": 1, "title": 1, "detail": 1, "due": 1, "priority": 1}
            ))
            if docs:
                return docs
    except Exception:
        pass

    try:
        with _engine().begin() as conn:
            rows = conn.execute(
                select(
                    custom_tasks.c.item_key,
                    custom_tasks.c.source,
                    custom_tasks.c.kind,
                    custom_tasks.c.title,
                    custom_tasks.c.detail,
                    custom_tasks.c.due,
                    custom_tasks.c.priority,
                ).where(custom_tasks.c.is_done == 0)
            ).mappings().all()
            return [dict(r) for r in rows]
    except Exception:  # noqa: BLE001
        return []


def list_custom_tasks(include_done: bool = False) -> list[dict]:
    """Return user-defined tasks (alias for get_active_custom_tasks)."""
    return get_active_custom_tasks()


def mark_task_done(source: str, title: str, due: str | None = None, kind: str = "task") -> bool:
    """Mark any task (custom or from MCP) as completed and reward the habit streak."""
    key = item_key(source, title, due)
    now = _now()
    try:
        mdb = _mongo_db()
        if mdb is not None:
            mdb["custom_tasks"].update_one(
                {"item_key": key},
                {"$set": {"is_done": 1}}
            )
            mdb["feedback"].insert_one({
                "ts": now.isoformat(),
                "item_key": key,
                "source": source,
                "kind": kind,
                "title": title,
                "action": "done",
            })
    except Exception:
        pass

    try:
        with _engine().begin() as conn:
            conn.execute(
                update(custom_tasks)
                .where(custom_tasks.c.item_key == key)
                .values(is_done=1)
            )
            conn.execute(
                insert(feedback),
                [{
                    "ts": now,
                    "item_key": key,
                    "source": source,
                    "kind": kind,
                    "title": title,
                    "action": "done",
                }],
            )
        return True
    except Exception:  # noqa: BLE001
        return False


def delete_custom_task(item_key_str: str) -> bool:
    """Delete a custom task by its item key."""
    try:
        mdb = _mongo_db()
        if mdb is not None:
            mdb["custom_tasks"].delete_one({"item_key": item_key_str})
    except Exception:
        pass

    try:
        with _engine().begin() as conn:
            conn.execute(delete(custom_tasks).where(custom_tasks.c.item_key == item_key_str))
        return True
    except Exception:  # noqa: BLE001
        return False


def get_done_item_keys() -> set[str]:
    """Return keys of all items marked as done."""
    keys: set[str] = set()
    try:
        mdb = _mongo_db()
        if mdb is not None:
            for d in mdb["custom_tasks"].find({"is_done": 1}, {"item_key": 1, "_id": 0}):
                if k := d.get("item_key"):
                    keys.add(k)
            for d in mdb["feedback"].find({"action": "done"}, {"item_key": 1, "_id": 0}):
                if k := d.get("item_key"):
                    keys.add(k)
    except Exception:
        pass

    try:
        with _engine().begin() as conn:
            fb_done = conn.execute(
                select(feedback.c.item_key).where(feedback.c.action == "done")
            ).scalars().all()
            task_done = conn.execute(
                select(custom_tasks.c.item_key).where(custom_tasks.c.is_done == 1)
            ).scalars().all()
            keys.update(fb_done)
            keys.update(task_done)
    except Exception:  # noqa: BLE001
        pass
    return keys


