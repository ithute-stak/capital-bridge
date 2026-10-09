"""Explicit server-side preflight for Ithute Auth rollout, without login activation.

A successful preflight is a *necessary*, never sufficient, rollout criterion.
No network calls or secrets are exposed to the browser.
"""
from __future__ import annotations

from dataclasses import dataclass

from api.ithute_auth_provider import IthuteAuthConfiguration, PRODUCTION_CALLBACK
from api.login_db import LoginDatabaseSettings


@dataclass(frozen=True)
class ActivationPreflight:
    callback: str
    dedicated_roles_configured: bool
    ready_for_manual_e2e_review: bool


def check_static_ithute_auth_prerequisites() -> ActivationPreflight:
    """Raise on missing/incorrect configuration; never enable the login router."""
    cfg = IthuteAuthConfiguration.from_environment()
    db = LoginDatabaseSettings.from_environment()
    if len({db.transactions, db.identities, db.sessions}) != 3:
        raise RuntimeError("Authentication roles must have separate credentials")
    if cfg.provider.redirect_uri != PRODUCTION_CALLBACK:
        raise RuntimeError("Production callback does not match the registered URL")
    return ActivationPreflight(
        callback=PRODUCTION_CALLBACK,
        dedicated_roles_configured=True,
        ready_for_manual_e2e_review=True,
    )
