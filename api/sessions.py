"""Server-side session primitives for a future OIDC backend-for-frontend.

The opaque cookie contains a random identifier only. Session credentials are
stored server side (future integration must use a shared encrypted store).
This module does not implement or enable a login endpoint.
"""
from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from uuid import UUID

SESSION_COOKIE = "__Host-cb_session"
SESSION_TTL = timedelta(hours=8)


@dataclass(frozen=True)
class Session:
    subject: UUID
    created_at: datetime
    expires_at: datetime


def create_session(subject: UUID, now: datetime | None = None) -> tuple[str, str, Session]:
    """Return cookie value, hashed storage key and server-side session."""
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError("timezone-aware datetime required")
    cookie = secrets.token_urlsafe(32)
    fingerprint = hashlib.sha256(cookie.encode("ascii")).hexdigest()
    return cookie, fingerprint, Session(subject, now, now + SESSION_TTL)


def session_key(cookie: str) -> str:
    if not cookie or len(cookie) > 256:
        raise ValueError("invalid session identifier")
    return hashlib.sha256(cookie.encode("ascii")).hexdigest()


def session_active(session: Session, now: datetime | None = None) -> bool:
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError("timezone-aware datetime required")
    return session.created_at <= now < session.expires_at


def cookie_options() -> dict:
    return {"key": SESSION_COOKIE, "httponly": True, "secure": True,
            "samesite": "strict", "path": "/", "max_age": int(SESSION_TTL.total_seconds())}


def check_same_origin(origin: str | None, expected_origin: str) -> bool:
    """Simple CSRF boundary for state-changing requests (not full CSRF protection)."""
    from urllib.parse import urlsplit
    if not origin:
        return False
    try:
        seen = urlsplit(origin)
        expected = urlsplit(expected_origin)
        return (seen.scheme == expected.scheme == "https"
                and seen.netloc == expected.netloc
                and seen.path in ("", "/") and not seen.query and not seen.fragment)
    except ValueError:
        return False
