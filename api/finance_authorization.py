"""Single finance authorization boundary for verified user subjects.

Both JWT and server-managed session authentication must resolve to a UUID before
this service checks company membership under transaction-local PostgreSQL RLS.
This module does not enable cookie-based access in public routes.
"""
from __future__ import annotations
from uuid import UUID
from fastapi import HTTPException


def require_company_membership(connection, *, company_id: UUID, user_id: UUID) -> None:
    """Set request context locally and verify an exact membership.

    Database role must be least-privilege and must NOT bypass RLS.
    """
    connection.execute("SELECT set_config('app.company_id', %s, true)", (str(company_id),))
    connection.execute("SELECT set_config('app.user_id', %s, true)", (str(user_id),))
    row=connection.execute(
        "SELECT 1 FROM cb.memberships WHERE company_id=%s AND user_id=%s",
        (company_id,user_id),
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=403,detail="Company access denied")
