"""Server-side session identity bridge for future authenticated finance requests.

Session cookies contain no user identity; the backend resolves the session
using a dedicated, role-checked database connection. Unregistered by default.
"""
from __future__ import annotations

from uuid import UUID
from fastapi import Cookie, HTTPException
from api.login_db import LoginDatabaseSettings, authentication_connection
from api.session_store import resolve
from api.sessions import SESSION_COOKIE


def resolve_finance_session(
    session_cookie: str | None, *,
    settings: LoginDatabaseSettings,
) -> UUID:
    if not session_cookie:
        raise HTTPException(status_code=401, detail="Authentication required")
    try:
        with authentication_connection(settings.sessions, purpose="sessions") as connection:
            subject = resolve(connection, session_cookie)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail="Invalid session") from exc
    if subject is None:
        raise HTTPException(status_code=401, detail="Session expired or revoked")
    return subject


def finance_cookie_identity(
    session_cookie: str | None = Cookie(default=None, alias=SESSION_COOKIE),
) -> UUID:
    """Staging dependency; no route mounts it until cookie auth is approved."""
    settings = LoginDatabaseSettings.from_environment()
    return resolve_finance_session(session_cookie, settings=settings)
