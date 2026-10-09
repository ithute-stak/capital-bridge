"""Server-side trusted OIDC login orchestration.

This service is not exposed as an HTTP endpoint until secure browser binding,
trusted callback handling and deployment-specific configuration are established.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Callable

from api.oidc_exchange import OidcProvider, exchange_and_verify
from api.oidc_transaction_store import consume
from api.identity_mapping import resolve_registered_user
from api.session_store import issue


@dataclass(frozen=True)
class LoginResult:
    session_cookie: str


def complete_verified_login(
    *,
    tx_db,
    user_db,
    session_db,
    provider: OidcProvider,
    browser_binding: str,
    state: str,
    code: str,
    http_client,
) -> LoginResult | None:
    """Consumes OIDC transaction BEFORE outbound exchange; rejects unknown users.

    tx_db MUST be a dedicated transaction/connection supporting commit and
    cannot be used for other business writes. Its consumption is committed before
    any external HTTP request, preventing replay after downstream errors.
    """
    transaction = consume(tx_db, state, browser_binding)
    if transaction is None:
        return None
    tx_db.commit()  # required: one-time consumption cannot roll back on exchange failure
    verified = exchange_and_verify(provider, transaction, state, code, client=http_client)
    subject = resolve_registered_user(user_db, verified)
    if subject is None:
        return None
    cookie = issue(session_db, subject)
    session_db.commit()
    return LoginResult(session_cookie=cookie)
