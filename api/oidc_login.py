"""Server-side OIDC Authorization Code + PKCE transaction validation.

This library deliberately does NOT issue sessions until the authorization code
is exchanged and the ID token is fully verified by a trusted callback handler.
"""
from __future__ import annotations
import hashlib
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

MAX_AGE=timedelta(minutes=5)

def random_urlsafe() -> str:
    return secrets.token_urlsafe(32)

def challenge(verifier: str) -> str:
    import base64
    digest=hashlib.sha256(verifier.encode("ascii")).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")

@dataclass(frozen=True)
class LoginTransaction:
    state: str
    nonce: str
    verifier: str
    created_at: datetime

def begin(authorization_endpoint: str, client_id: str, redirect_uri: str, scopes=("openid","profile"), now=None):
    from urllib.parse import urlsplit
    auth=urlsplit(authorization_endpoint)
    redirect=urlsplit(redirect_uri)
    if (auth.scheme!="https" or redirect.scheme!="https" or
        not auth.netloc or not redirect.netloc or not client_id or "openid" not in scopes):
        raise ValueError("trusted HTTPS OIDC configuration is required")
    now=now or datetime.now(timezone.utc)
    if now.tzinfo is None: raise ValueError("timezone-aware timestamp required")
    tx=LoginTransaction(random_urlsafe(),random_urlsafe(),random_urlsafe(),now)
    params=urlencode({"response_type":"code","client_id":client_id,
        "redirect_uri":redirect_uri,"scope":" ".join(scopes),
        "state":tx.state,"nonce":tx.nonce,
        "code_challenge":challenge(tx.verifier),"code_challenge_method":"S256"})
    separator="&" if auth.query else "?"
    return authorization_endpoint+separator+params,tx

def verify_callback(tx: LoginTransaction, state: str, code: str, now=None) -> str:
    now=now or datetime.now(timezone.utc)
    if not code or not state or not secrets.compare_digest(state,tx.state):
        raise ValueError("invalid OIDC callback state or code")
    if tx.created_at>now or now-tx.created_at>MAX_AGE:
        raise ValueError("expired OIDC login transaction")
    return tx.verifier
