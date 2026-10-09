"""Database connection boundaries for a future OIDC backend-for-frontend.

Each authentication purpose uses a separate restricted PostgreSQL credential.
Connections are short lived, rolled back on failure and never shared across
browser requests. This factory is not yet wired into the live login router.
"""
from __future__ import annotations
import os
from contextlib import contextmanager
from dataclasses import dataclass
import psycopg

ENV_KEYS = {
    "transactions": "CB_OIDC_TRANSACTION_DATABASE_URL",
    "identities": "CB_IDENTITY_DATABASE_URL",
    "sessions": "CB_SESSION_DATABASE_URL",
}

@dataclass(frozen=True)
class LoginDatabaseSettings:
    transactions: str
    identities: str
    sessions: str

    @classmethod
    def from_environment(cls) -> "LoginDatabaseSettings":
        entries = {purpose: os.getenv(env, "") for purpose, env in ENV_KEYS.items()}
        if any(not value for value in entries.values()):
            raise RuntimeError("Dedicated authentication database URLs are required")
        if len(set(entries.values())) != len(entries):
            raise RuntimeError("Authentication database credentials must be isolated")
        return cls(**entries)

@contextmanager
def authentication_connection(dsn: str, *, readonly: bool = False):
    """Yield an independent transaction; commit only successful work."""
    with psycopg.connect(dsn, autocommit=False, connect_timeout=5) as connection:
        try:
            # Never rely on a previous request's database session settings.
            connection.execute("SET LOCAL statement_timeout = '5000ms'")
            connection.execute("SET LOCAL lock_timeout = '2000ms'")
            if readonly:
                connection.execute("SET TRANSACTION READ ONLY")
            yield connection
            connection.commit()
        except BaseException:
            connection.rollback()
            raise
