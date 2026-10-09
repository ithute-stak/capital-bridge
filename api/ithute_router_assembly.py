"""Unactivated Ithute Auth router assembly.

Keep separate from api.main until production callback, session verification,
logout and full end-to-end tests are approved.
"""
from api.ithute_oidc_router import make_ithute_oidc_router
from api.ithute_runtime_factory import ithute_login_service

staged_ithute_router = make_ithute_oidc_router(ithute_login_service)
