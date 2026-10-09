"""One-time OIDC transaction persistence for trusted backend callers.

A short-lived HttpOnly Secure browser-binding cookie is mandatory at callback.
The session created after verified code exchange is separate from this cookie.
"""
from __future__ import annotations
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID

from api.oidc_login import LoginTransaction

LOGIN_MAX_AGE = timedelta(minutes=5)
BINDING_COOKIE = "__Host-cb_oidc"
def digest(value: str) -> str:
    if not isinstance(value, str) or not value or len(value) > 512:
        raise ValueError("invalid transaction identifier")
    return hashlib.sha256(value.encode("utf-8")).hexdigest()

def new_binding() -> str:
    return secrets.token_urlsafe(32)

def store(db, tx: LoginTransaction, binding: str) -> None:
    db.execute(
        "INSERT INTO cb.oidc_login_transactions "
        "(state_hash,binding_hash,nonce,verifier,created_at,expires_at) VALUES (%s,%s,%s,%s,%s,%s)",
        (digest(tx.state), digest(binding), tx.nonce, tx.verifier, tx.created_at,
         tx.created_at + LOGIN_MAX_AGE),
    )

def consume(db, state: str, binding: str, now: datetime | None = None) -> LoginTransaction | None:
    """Atomic first-consumer-wins update; caller must commit before code exchange."""
    try:
        state_hash, binding_hash = digest(state), digest(binding)
    except (ValueError, UnicodeError):
        return None
    now = now or datetime.now(timezone.utc)
    row = db.execute(
        "UPDATE cb.oidc_login_transactions SET consumed_at=%s "
        "WHERE state_hash=%s AND binding_hash=%s AND consumed_at IS NULL "
        "AND created_at<=%s AND expires_at>%s "
        "RETURNING nonce,verifier,created_at",
        (now,state_hash,binding_hash,now,now),
    ).fetchone()
    if row is None:
        return None
    return LoginTransaction(state=state,nonce=row[0],verifier=row[1],created_at=row[2])

def clear_expired(db, now: datetime | None = None) -> int:
    now = now or datetime.now(timezone.utc)
    return db.execute(
        "DELETE FROM cb.oidc_login_transactions WHERE expires_at<=%s OR consumed_at IS NOT NULL",
        (now,),
    ).rowcount
