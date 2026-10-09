"""Opt-in HTTP OIDC flow with deliberately disabled activation.

The begin/callback endpoints default to HTTP 503. Deployment must explicitly
supply trusted dependencies for IdP config and separate restricted databases.
No endpoints are registered into the main application by this module.
"""
from __future__ import annotations

from dataclasses import dataclass
from fastapi import APIRouter, Cookie, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from api.oidc_callback_guards import validate_callback, callback_cookie_settings, callback_response_headers
from api.oidc_transaction_store import BINDING_COOKIE
from api.oidc_initiation import initiate_login
from api.login_orchestration import complete_verified_login
from api.sessions import cookie_options

router = APIRouter(prefix="/api/v1/oidc", tags=["oidc"])
_runtime = None


@dataclass(frozen=True)
class TrustedRuntime:
    """Injected only by trusted server bootstrap, never via an HTTP header."""
    authorization_endpoint: str
    client_id: str
    redirect_uri: str
    provider: object
    transaction_connection: object
    user_connection: object
    session_connection: object
    http_client: object


def configure_for_testing(runtime: TrustedRuntime | None):
    """Test seam, NOT an authorization or production configuration endpoint."""
    global _runtime
    _runtime = runtime


def runtime_or_unavailable() -> TrustedRuntime:
    if _runtime is None:
        raise HTTPException(status_code=503, detail="OIDC login not configured")
    return _runtime


@router.get("/start")
def start():
    rt = runtime_or_unavailable()
    result = initiate_login(
        db=rt.transaction_connection,
        authorization_endpoint=rt.authorization_endpoint,
        client_id=rt.client_id,
        redirect_uri=rt.redirect_uri,
    )
    response = RedirectResponse(result.authorization_url, status_code=303)
    response.set_cookie(value=result.browser_binding, **callback_cookie_settings())
    response.headers.update(callback_response_headers())
    return response


@router.get("/complete")
def complete(
    state: str | None = Query(default=None),
    code: str | None = Query(default=None),
    error: str | None = Query(default=None),
    browser_binding: str | None = Cookie(default=None, alias=BINDING_COOKIE),
):
    rt = runtime_or_unavailable()
    verified = validate_callback(state=state, code=code,
                                 browser_binding=browser_binding, error=error)
    result = complete_verified_login(
        tx_db=rt.transaction_connection,
        user_db=rt.user_connection,
        session_db=rt.session_connection,
        provider=rt.provider,
        browser_binding=verified.browser_binding,
        state=verified.state, code=verified.code,
        http_client=rt.http_client,
    )
    if result is None:
        raise HTTPException(status_code=401, detail="Authentication failed")
    response = RedirectResponse("/", status_code=303)
    response.set_cookie(value=result.session_cookie, **cookie_options())
    response.delete_cookie(BINDING_COOKIE, path="/", secure=True, httponly=True, samesite="lax")
    response.headers.update(callback_response_headers())
    return response
