"""Resolve cryptographically verified OIDC identity to a pre-provisioned user.

NEVER create users here or map solely by unverified email.
"""
from __future__ import annotations
from uuid import UUID
from api.oidc_verify import TrustedIdentity


def resolve_registered_user(db, identity: TrustedIdentity) -> UUID | None:
    if not identity.issuer.startswith("https://") or not identity.subject:
        return None
    row = db.execute(
        "SELECT user_id FROM cb.external_identities WHERE issuer=%s AND subject=%s",
        (identity.issuer, identity.subject),
    ).fetchone()
    return row[0] if row else None
