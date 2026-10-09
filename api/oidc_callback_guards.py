"""Fail-closed request guards for a future server-side OIDC callback.

This module does not handle tokens or issue login sessions. It validates the
callback parameters and browser binding before invoking the one-time store.
"""
from __future__ import annotations
from dataclasses import dataclass
from urllib.parse import urlsplit
import secrets

from fastapi import HTTPException
from api.oidc_transaction_store import BINDING_COOKIE

MAX_CODE_LENGTH = 4096
MAX_STATE_LENGTH = 512

@dataclass(frozen=True)
class CallbackInput:
    state: str
    code: str
    browser_binding: str

def validate_callback(
    *,
    state: str | None,
    code: str | None,
    browser_binding: str | None,
    error: str | None = None,
    error_description: str | None = None,
) -> CallbackInput:
    if error is not None:
        raise HTTPException(status_code=401, detail="Identity provider rejected sign-in")
    if (not isinstance(state,str) or not isinstance(code,str)
        or not isinstance(browser_binding,str)
        or not 16 <= len(state) <= MAX_STATE_LENGTH
        or not 1 <= len(code) <= MAX_CODE_LENGTH
        or not 16 <= len(browser_binding) <= MAX_STATE_LENGTH
        or any(ord(ch) < 33 or ord(ch) > 126 for ch in state+code+browser_binding)):
        raise HTTPException(status_code=400, detail="Invalid authentication callback")
    return CallbackInput(state=state,code=code,browser_binding=browser_binding)

def callback_cookie_settings() -> dict:
    return {
        "key": BINDING_COOKIE,
        "secure": True,
        "httponly": True,
        "samesite": "lax",  # allow top-level cross-site navigation from IdP
        "path": "/",
        "max_age": 300,
    }

def callback_response_headers() -> dict[str,str]:
    return {
        "Cache-Control": "no-store",
        "Pragma": "no-cache",
        "Referrer-Policy": "no-referrer",
        "X-Content-Type-Options": "nosniff",
    }
