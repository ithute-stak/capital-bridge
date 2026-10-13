"""Trusted server-owned tenant mapping for future consultation intake.

No public endpoint calls this helper yet. Never derive a tenant from JSON fields,
Origin, Host headers, arbitrary query strings, or browser-provided credentials.
"""
from __future__ import annotations

import os
from uuid import UUID

APPROVED_PUBLIC_SITE = "https://capitalbridge.co.ls"


def consultation_company_id() -> UUID:
    """Resolve the sole approved intake company from deployment-owned config.

    Fail closed if the explicit tenant ID is absent, malformed or nil.
    This does not authorize a write by itself; restricted DB role and RLS,
    edge protections, origin protections and retention review remain required.
    """
    value = os.environ.get("CB_CONSULTATION_COMPANY_ID", "").strip()
    if not value:
        raise RuntimeError("Approved consultation intake company is not configured")
    try:
        company_id = UUID(value)
    except (ValueError, AttributeError) as exc:
        raise RuntimeError("Approved consultation intake company is invalid") from exc
    if company_id.int == 0:
        raise RuntimeError("Approved consultation intake company cannot be zero UUID")
    return company_id
