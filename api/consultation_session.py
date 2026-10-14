"""Cookie-backed staff consultation BFF.

The opaque HttpOnly session is resolved server-side. Browser JavaScript never
sees the session value. OIDC session issuance remains deployment-gated.
"""
from __future__ import annotations

import os
from uuid import UUID

import psycopg
from fastapi import APIRouter, Cookie, Depends, Header, HTTPException, Query
from psycopg.rows import dict_row

from api.sessions import SESSION_COOKIE, check_same_origin
from api.session_store import resolve
from api.login_db import LoginDatabaseSettings, authentication_connection
from api.main import config
from api.consultations import (
    ConsultationStatusChange, list_consultations, update_consultation_status,
)

router = APIRouter(prefix="/api/v1/staff/consultations", tags=["staff-consultations"])


def staff_session_subject(
    cb_session: str | None = Cookie(default=None, alias=SESSION_COOKIE),
) -> UUID:
    if not cb_session:
        raise HTTPException(status_code=401, detail="Staff sign-in required")
    try:
        settings = LoginDatabaseSettings.from_environment()
        with authentication_connection(settings.sessions, purpose="sessions") as db:
            user_id = resolve(db, cb_session)
    except (RuntimeError, ValueError, psycopg.Error):
        raise HTTPException(status_code=401, detail="Staff sign-in required") from None
    if not isinstance(user_id, UUID) or user_id.int == 0:
        raise HTTPException(status_code=401, detail="Staff sign-in required")
    return user_id


def require_staff_origin(origin: str | None) -> None:
    expected = os.environ.get("CB_PUBLIC_ORIGIN", "")
    if expected != "https://capitalbridge.co.ls" or not check_same_origin(origin, expected):
        raise HTTPException(status_code=403, detail="Invalid staff request origin")


@router.get("/companies")
def staff_companies(user_id: UUID = Depends(staff_session_subject)):
    _, _, _, dsn = config()
    with psycopg.connect(dsn, row_factory=dict_row, autocommit=False) as db:
        with db.transaction():
            db.execute("SELECT set_config('app.user_id',%s,true)", (str(user_id),))
            records = db.execute(
                "SELECT company_id,legal_name,role FROM cb.list_my_companies()"
            ).fetchall()
    return {"companies": [{
        "id": str(row["company_id"]), "name": row["legal_name"],
        "role": row["role"]
    } for row in records]}


@router.get("/companies/{company_id}/enquiries")
def staff_enquiries(
    company_id: UUID,
    limit: int = Query(default=30, ge=1, le=100),
    user_id: UUID = Depends(staff_session_subject),
):
    return list_consultations(company_id=company_id, limit=limit, user_id=user_id)


@router.patch("/companies/{company_id}/enquiries/{enquiry_id}/status")
def staff_update_status(
    company_id: UUID,
    enquiry_id: UUID,
    payload: ConsultationStatusChange,
    origin: str | None = Header(default=None),
    user_id: UUID = Depends(staff_session_subject),
):
    require_staff_origin(origin)
    return update_consultation_status(
        company_id=company_id, enquiry_id=enquiry_id,
        payload=payload, user_id=user_id,
    )
