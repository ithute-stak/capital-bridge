"""Server-side OIDC authorization-code exchange and verified identity composition.

This module has no HTTP login endpoint and issues no session cookies.
The caller must consume a one-time server-stored login transaction before
exchanging the code, and map the returned issuer/subject against a trusted
internal identity registry.
"""
from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlsplit

import httpx

from api.oidc_login import LoginTransaction, verify_callback
from api.oidc_verify import TrustedIdentity, verify_id_token


@dataclass(frozen=True)
class OidcProvider:
    issuer: str
    token_endpoint: str
    jwks_url: str
    client_id: str
    redirect_uri: str

    def validate(self) -> None:
        locations = [urlsplit(value) for value in
                     (self.issuer, self.token_endpoint, self.jwks_url)]
        redirect = urlsplit(self.redirect_uri)
        if any(p.scheme != "https" or not p.hostname or p.username or p.password
               or p.fragment for p in locations):
            raise ValueError("Invalid provider URL")
        if any(p.netloc != locations[0].netloc for p in locations):
            raise ValueError("OIDC endpoints must have the pinned issuer origin")
        if redirect.scheme != "https" or not redirect.hostname or redirect.fragment:
            raise ValueError("Trusted HTTPS redirect URI required")
        if not self.client_id:
            raise ValueError("OIDC public client ID required")


def exchange_and_verify(
    provider: OidcProvider, tx: LoginTransaction, state: str, code: str,
    *, client: httpx.Client,
) -> TrustedIdentity:
    """Must only be called after atomic one-time transaction consumption.

    Injected HTTP client simplifies testing. Never accept token endpoint, issuer
    or redirect URI from request parameters.
    """
    provider.validate()
    verifier = verify_callback(tx, state, code)
    response = client.post(
        provider.token_endpoint,
        data={"grant_type": "authorization_code", "code": code,
              "redirect_uri": provider.redirect_uri,
              "client_id": provider.client_id, "code_verifier": verifier},
        headers={"Accept": "application/json"},
        timeout=8.0,
        follow_redirects=False,
    )
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict) or not isinstance(payload.get("id_token"), str):
        raise ValueError("OIDC exchange did not return a valid ID token")
    return verify_id_token(
        payload["id_token"], issuer=provider.issuer, client_id=provider.client_id,
        jwks_url=provider.jwks_url, expected_nonce=tx.nonce,
    )
