"""Request-scoped OIDC login service using restricted database roles.

This service is deliberately not registered as an HTTP endpoint. Database
transactions are released before outbound identity-provider network calls.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from api.identity_mapping import resolve_registered_user
from api.login_db import LoginDatabaseSettings, authentication_connection
from api.oidc_exchange import OidcProvider, exchange_and_verify
from api.oidc_initiation import initiate_login, LoginStart
from api.oidc_transaction_store import consume
from api.session_store import issue


@dataclass(frozen=True)
class LoginReceipt:
    cookie: str


class LoginService:
    def __init__(self, db: LoginDatabaseSettings, provider: OidcProvider,
                 authorization_endpoint: str, http_client: Any):
        provider.validate()
        if not authorization_endpoint.startswith(provider.issuer.rstrip("/") + "/"):
            raise ValueError("Authorization endpoint must belong to the trusted issuer")
        self.db = db
        self.provider = provider
        self.authorization_endpoint = authorization_endpoint
        self.http_client = http_client

    def begin(self) -> LoginStart:
        with authentication_connection(self.db.transactions, purpose="transactions") as connection:
            return initiate_login(
                db=connection, authorization_endpoint=self.authorization_endpoint,
                client_id=self.provider.client_id, redirect_uri=self.provider.redirect_uri,
            )

    def complete(self, *, state: str, code: str, browser_binding: str) -> LoginReceipt | None:
        # Consumption commits on exiting this context BEFORE any network call,
        # even if the IdP subsequently refuses the code.
        with authentication_connection(self.db.transactions, purpose="transactions") as connection:
            transaction = consume(connection, state, browser_binding)
        if transaction is None:
            return None

        identity = exchange_and_verify(
            self.provider, transaction, state, code, client=self.http_client,
        )
        with authentication_connection(self.db.identities, purpose="identities", readonly=True) as connection:
            user_id = resolve_registered_user(connection, identity)
        if user_id is None:
            return None
        with authentication_connection(self.db.sessions, purpose="sessions") as connection:
            cookie = issue(connection, user_id)
        return LoginReceipt(cookie=cookie)
