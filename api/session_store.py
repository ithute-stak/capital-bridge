"""Durable session storage operations for trusted server-side callers.

Never accept a user-selected subject or session key from the HTTP request.
Use a separate, narrowly privileged database role for session management.
"""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID
import psycopg
from psycopg.rows import dict_row

from api.sessions import create_session, session_key, session_active, Session


def issue(db: psycopg.Connection, subject: UUID, now: datetime | None = None) -> str:
    cookie, key, entry = create_session(subject, now)
    db.execute(
        "INSERT INTO cb.user_sessions(key_hash,subject,created_at,expires_at) VALUES (%s,%s,%s,%s)",
        (key, entry.subject, entry.created_at, entry.expires_at),
    )
    return cookie


def resolve(db: psycopg.Connection, cookie: str, now: datetime | None = None) -> UUID | None:
    try:
        key = session_key(cookie)
    except (ValueError, UnicodeEncodeError):
        return None
    now = now or datetime.now(timezone.utc)
    row = db.execute(
        "SELECT subject,created_at,expires_at FROM cb.user_sessions "
        "WHERE key_hash=%s AND revoked_at IS NULL AND expires_at>%s",
        (key, now),
    ).fetchone()
    if row is None:
        return None
    entry = Session(row[0], row[1], row[2])
    return entry.subject if session_active(entry, now) else None


def revoke(db: psycopg.Connection, cookie: str, now: datetime | None = None) -> bool:
    try:
        key = session_key(cookie)
    except (ValueError, UnicodeEncodeError):
        return False
    now = now or datetime.now(timezone.utc)
    cursor = db.execute(
        "UPDATE cb.user_sessions SET revoked_at=%s "
        "WHERE key_hash=%s AND revoked_at IS NULL", (now, key),
    )
    return cursor.rowcount == 1


def purge_expired(db: psycopg.Connection, now: datetime | None = None) -> int:
    now = now or datetime.now(timezone.utc)
    result = db.execute(
        "DELETE FROM cb.user_sessions WHERE expires_at<=%s OR revoked_at IS NOT NULL",
        (now,),
    )
    return result.rowcount
