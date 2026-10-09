"""Fail-closed BFF session endpoints.

Session issuance is intentionally not public until the trusted server-side
OIDC callback is implemented and cryptographic identity validation completed.
"""
from __future__ import annotations

import os
from fastapi import APIRouter, Cookie, Header, HTTPException, Response
from api.sessions import SESSION_COOKIE, check_same_origin
from api.session_store import resolve, revoke
from api.login_db import LoginDatabaseSettings, authentication_connection

router = APIRouter(prefix="/api/v1/session", tags=["session"])


def session_database_url() -> str:
    return LoginDatabaseSettings.from_environment().sessions


@router.get("/status")
def status(cb_session: str | None = Cookie(default=None, alias=SESSION_COOKIE)):
    if not cb_session:
        return {"authenticated": False}
    settings = LoginDatabaseSettings.from_environment()
    with authentication_connection(settings.sessions, purpose="sessions") as db:
        subject = resolve(db, cb_session)
    # Deliberately do not reveal the subject to the browser.
    return {"authenticated": subject is not None}


@router.post("/logout")
def logout(
    response: Response,
    cb_session: str | None = Cookie(default=None, alias=SESSION_COOKIE),
    origin: str | None = Header(default=None),
):
    expected_origin = os.getenv("CB_PUBLIC_ORIGIN", "")
    if not expected_origin or not check_same_origin(origin, expected_origin):
        raise HTTPException(status_code=403, detail="Origin verification failed")
    if cb_session:
        settings = LoginDatabaseSettings.from_environment()
        with authentication_connection(settings.sessions, purpose="sessions") as db:
            revoke(db, cb_session)
    response.delete_cookie(SESSION_COOKIE, path="/", secure=True, httponly=True, samesite="strict")
    response.headers["Cache-Control"] = "no-store"
    return {"authenticated": False}


@router.post("/login")
def login_unavailable():
    # Never accept an unverified browser-provided subject.
    raise HTTPException(status_code=503, detail="Trusted identity provider login is not configured")
