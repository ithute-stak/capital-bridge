"""Server-only login initiation. The resulting URL is for a trusted OIDC IdP.

This helper must be called by a protected, HTTPS backend route, with a dedicated
transaction database role, CSRF policy and a trusted static provider config.
"""
from __future__ import annotations

from dataclasses import dataclass
from api.oidc_login import begin
from api.oidc_transaction_store import new_binding,store,BINDING_COOKIE

@dataclass(frozen=True)
class LoginStart:
    authorization_url: str
    browser_binding: str

def initiate_login(*, db, authorization_endpoint: str, client_id: str,
                   redirect_uri: str) -> LoginStart:
    url, transaction = begin(authorization_endpoint,client_id,redirect_uri)
    binding = new_binding()
    store(db,transaction,binding)
    db.commit()  # persist transaction before browser leaves for IdP
    return LoginStart(authorization_url=url,browser_binding=binding)
