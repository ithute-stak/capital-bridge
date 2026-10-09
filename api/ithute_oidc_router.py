"""Request-scoped Ithute Auth OIDC router factory.

Not mounted in api.main. The caller must provide a trusted, audited service
factory during server bootstrap, never through client-controlled data.
"""
from __future__ import annotations
from typing import Callable
from fastapi import APIRouter, Cookie, HTTPException, Query
from fastapi.responses import RedirectResponse
from api.oidc_callback_guards import (
    validate_callback, callback_cookie_settings, callback_response_headers,
)
from api.oidc_transaction_store import BINDING_COOKIE
from api.sessions import cookie_options
from api.login_service import LoginService


def make_ithute_oidc_router(service_factory: Callable[[], LoginService]) -> APIRouter:
    router = APIRouter(prefix="/api/v1/oidc", tags=["oidc"])

    def trusted_service() -> LoginService:
        service = service_factory()
        if not isinstance(service, LoginService):
            raise HTTPException(status_code=503, detail="Ithute authentication unavailable")
        return service

    @router.get("/start")
    def start():
        result = trusted_service().begin()
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
        verified = validate_callback(
            state=state, code=code, browser_binding=browser_binding, error=error,
        )
        result = trusted_service().complete(
            state=verified.state, code=verified.code,
            browser_binding=verified.browser_binding,
        )
        if result is None:
            raise HTTPException(status_code=401, detail="Authentication failed")
        response = RedirectResponse("/", status_code=303)
        response.set_cookie(value=result.cookie, **cookie_options())
        response.delete_cookie(
            BINDING_COOKIE, path="/", secure=True, httponly=True, samesite="lax",
        )
        response.headers.update(callback_response_headers())
        return response

    return router
