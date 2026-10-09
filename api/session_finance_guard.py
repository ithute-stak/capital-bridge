"""Staged company-scoped finance access using verified server sessions.

No finance route imports this module yet. The session role only resolves the
user; finance authorization always happens on a separate finance connection.
"""
from __future__ import annotations

from contextlib import contextmanager
from uuid import UUID

import psycopg
from fastapi import HTTPException

from api.finance_authorization import require_company_membership
from api.finance_session_auth import resolve_finance_session
from api.login_db import LoginDatabaseSettings


@contextmanager
def authorized_finance_session(
    *, company_id: UUID, cookie: str | None,
    session_settings: LoginDatabaseSettings, finance_dsn: str,
):
    """Yield a transaction-limited finance connection after both checks.

    The caller must not use the raw session cookie as a principal, accept
    browser-provided user IDs, or reuse this connection for another company.
    """
    if not finance_dsn:
        raise RuntimeError("Finance database URL is required")
    user_id = resolve_finance_session(cookie, settings=session_settings)
    with psycopg.connect(finance_dsn, autocommit=False) as connection:
        with connection.transaction():
            require_company_membership(
                connection, company_id=company_id, user_id=user_id,
            )
            yield connection
