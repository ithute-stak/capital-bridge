"""HTTP callback staging route: intentionally disabled until IdP configured.

Rejects unsolicited callbacks, never accepts an unverified subject and never
creates a session. A real rollout must replace this route only after end-to-end
OIDC verification and transaction/session database role provisioning.
"""
from __future__ import annotations
from fastapi import APIRouter, Cookie, Query, Response
from api.oidc_callback_guards import (
    validate_callback, callback_response_headers, callback_cookie_settings,
)
from api.oidc_transaction_store import BINDING_COOKIE

router = APIRouter(prefix="/api/v1/oidc", tags=["oidc"])

@router.get("/callback", status_code=503)
def callback_staged(
    response: Response,
    state: str | None = Query(default=None),
    code: str | None = Query(default=None),
    error: str | None = Query(default=None),
    browser_binding: str | None = Cookie(default=None, alias=BINDING_COOKIE),
):
    response.headers.update(callback_response_headers())
    # A binding cookie must exist, and the callback must be well-formed.
    validate_callback(state=state,code=code,browser_binding=browser_binding,error=error)
    response.delete_cookie(BINDING_COOKIE, path="/", secure=True, httponly=True, samesite="lax")
    return {"detail": "OIDC callback is not enabled; no session issued"}
