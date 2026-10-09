"""Pinned configuration for Ithute Auth as the CapitalBridge OIDC identity provider.

Configuration is server-side only; this does not activate any login endpoint.
"""
from __future__ import annotations

import os
from urllib.parse import urlsplit
from dataclasses import dataclass

from api.oidc_exchange import OidcProvider

ISSUER = "https://auth.ithute.co.ls"
CLIENT_ID = "capitalbridge"
AUTHORIZATION_ENDPOINT = ISSUER + "/oauth/authorize"
TOKEN_ENDPOINT = ISSUER + "/oauth/token"
JWKS_URL = ISSUER + "/.well-known/jwks.json"
CALLBACK_PATH = "/api/v1/oidc/complete"


@dataclass(frozen=True)
class IthuteAuthConfiguration:
    provider: OidcProvider
    authorization_endpoint: str

    @classmethod
    def from_environment(cls) -> "IthuteAuthConfiguration":
        callback = os.environ.get("CB_ITHUTE_OIDC_REDIRECT_URI", "")
        parsed = urlsplit(callback)
        if (
            parsed.scheme != "https" or not parsed.hostname
            or parsed.username or parsed.password or parsed.query or parsed.fragment
            or parsed.path != CALLBACK_PATH
        ):
            raise RuntimeError("Exact HTTPS CapitalBridge OIDC callback URI is required")
        # Deployment must register callback verbatim on the Ithute Auth side.
        provider = OidcProvider(
            issuer=ISSUER,
            token_endpoint=TOKEN_ENDPOINT,
            jwks_url=JWKS_URL,
            client_id=CLIENT_ID,
            redirect_uri=callback,
        )
        provider.validate()
        return cls(provider=provider, authorization_endpoint=AUTHORIZATION_ENDPOINT)
