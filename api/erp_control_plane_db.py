"""Strict configuration checks for a future isolated ERP control-plane DB.

Not an enabled transport or connection pool. A separately authenticated gateway
must derive operator identity from verified OIDC and restrict SQL capabilities.
"""
from __future__ import annotations

import os
from urllib.parse import urlsplit, parse_qs


def control_plane_dsn(environ=None) -> str:
    source = os.environ if environ is None else environ
    dedicated = source.get("CB_ERP_CONTROL_PLANE_DATABASE_URL", "").strip()
    finance = source.get("CB_DATABASE_URL", "").strip()
    if not dedicated or not finance:
        raise RuntimeError("Dedicated ERP control-plane and finance DSNs are required")
    if dedicated == finance:
        raise RuntimeError("Control-plane database credential cannot equal finance credential")
    parsed = urlsplit(dedicated)
    standard = urlsplit(finance)
    if parsed.scheme not in ("postgresql", "postgres") or standard.scheme not in ("postgresql", "postgres"):
        raise RuntimeError("PostgreSQL connection URLs required")
    if not parsed.username or not parsed.password or not parsed.hostname or not parsed.path.strip("/"):
        raise RuntimeError("Control-plane DSN must contain a dedicated login and database")
    if parsed.username == standard.username:
        raise RuntimeError("Control-plane database role must differ from finance database role")
    if parsed.password == standard.password:
        raise RuntimeError("Control-plane credential must differ from finance credential")
    if parsed.username in ("postgres", "root", "cb_erp_control_plane"):
        raise RuntimeError("Control-plane login must be a restricted LOGIN role, not a privileged or NOLOGIN group")
    if parsed.fragment or parsed.query:
        # Deployment review may separately support TLS query parameters; no
        # unreviewed connection options, including role-setting, are accepted.
        raise RuntimeError("Unreviewed control-plane connection options")
    return dedicated
