"""Trusted server-only Ithute Auth login service factory.

Prepared for audited application bootstrap; it is deliberately NOT mounted in
api.main and cannot be activated by user-supplied values.
"""
from __future__ import annotations

from contextlib import contextmanager
import httpx

from api.ithute_discovery import verify_ithute_discovery
from api.login_db import LoginDatabaseSettings
from api.login_service import LoginService


@contextmanager
def ithute_login_service():
    """Construct independently configured service, then release HTTP resources."""
    database = LoginDatabaseSettings.from_environment()
    with httpx.Client(
        timeout=8.0, follow_redirects=False, trust_env=False,
    ) as client:
        config = verify_ithute_discovery(client)
        yield LoginService(
            database, config.provider, config.authorization_endpoint, client,
        )
