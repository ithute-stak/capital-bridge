"""Validate remote Ithute OIDC discovery before any future login rollout.

Only probes the fixed HTTPS origin; never accepts a browser-supplied URL.
This module is not mounted on the API and does not enable live sign-in.
"""
from __future__ import annotations

from api.ithute_auth_provider import (
    ISSUER, AUTHORIZATION_ENDPOINT, TOKEN_ENDPOINT, JWKS_URL,
    IthuteAuthConfiguration,
)

DISCOVERY_URL = ISSUER + "/.well-known/openid-configuration"


def verify_ithute_discovery(client) -> IthuteAuthConfiguration:
    configured = IthuteAuthConfiguration.from_environment()
    response = client.get(
        DISCOVERY_URL, headers={"Accept": "application/json"},
        timeout=5.0, follow_redirects=False,
    )
    response.raise_for_status()
    data = response.json()
    if not isinstance(data, dict) or any((
        data.get("issuer") != ISSUER,
        data.get("authorization_endpoint") != AUTHORIZATION_ENDPOINT,
        data.get("token_endpoint") != TOKEN_ENDPOINT,
        data.get("jwks_uri") != JWKS_URL,
        "S256" not in data.get("code_challenge_methods_supported", []),
        "code" not in data.get("response_types_supported", []),
    )):
        raise RuntimeError("Ithute discovery metadata does not match pinned OIDC configuration")
    return configured
