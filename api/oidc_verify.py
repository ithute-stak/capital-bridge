"""Strict verification of OIDC ID tokens before any server-side session issuance.

The caller must pin a trusted issuer, expected public client ID and HTTPS JWKS URL.
ID tokens do not authorize finance API calls; this helper only authenticates the
OIDC login callback identity.
"""
from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlsplit

import jwt
from jwt import PyJWKClient


@dataclass(frozen=True)
class TrustedIdentity:
    issuer: str
    subject: str


def verify_id_token(
    token: str, *, issuer: str, client_id: str, jwks_url: str, expected_nonce: str,
) -> TrustedIdentity:
    if not token or not expected_nonce or not client_id:
        raise ValueError("Missing identity verification parameters")
    iss = urlsplit(issuer)
    keys = urlsplit(jwks_url)
    if (iss.scheme != "https" or keys.scheme != "https"
            or not iss.netloc or not keys.netloc
            or iss.netloc != keys.netloc or iss.fragment or keys.fragment):
        raise ValueError("Trusted HTTPS identity provider configuration required")
    try:
        key = PyJWKClient(jwks_url, cache_jwk_set=True, lifespan=300).get_signing_key_from_jwt(token).key
        claims = jwt.decode(
            token, key, algorithms=["RS256"], issuer=issuer, audience=client_id,
            options={"require": ["exp", "iat", "iss", "aud", "sub", "nonce"]},
            leeway=30,
        )
    except jwt.PyJWTError as exc:
        raise ValueError("Identity token signature or claims invalid") from exc
    if not isinstance(claims["nonce"], str) or not __import__("hmac").compare_digest(
        claims["nonce"], expected_nonce
    ):
        raise ValueError("Identity token nonce mismatch")
    if not isinstance(claims["sub"], str) or not claims["sub"]:
        raise ValueError("Identity token subject invalid")
    if "azp" in claims and claims["azp"] != client_id:
        raise ValueError("Identity token authorized party mismatch")
    if isinstance(claims.get("aud"), list) and len(claims["aud"]) > 1 and claims.get("azp") != client_id:
        raise ValueError("Identity token authorized party required")
    return TrustedIdentity(issuer=claims["iss"], subject=claims["sub"])
