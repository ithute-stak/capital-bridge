"""Authenticated, company-scoped consultation queue.

No public submission, no unauthenticated access, and no cross-company lookup.
Database runtime role must have explicit SELECT privileges and must not bypass RLS.
"""
from __future__ import annotations

from uuid import UUID
from typing import Literal
from pydantic import BaseModel, ConfigDict
import psycopg
from psycopg.rows import dict_row
from fastapi import APIRouter, Depends, Query, HTTPException

from api.main import authenticate, config, validate_company
from api.consultation_events import publish_consultation_change

router = APIRouter(prefix="/api/v1/companies/{company_id}/consultations", tags=["consultations"])


@router.get("")
def list_consultations(
    company_id: UUID,
    limit: int = Query(default=30, ge=1, le=100),
    user_id: UUID = Depends(authenticate),
):
    _, _, _, dsn = config()
    with psycopg.connect(dsn, row_factory=dict_row, autocommit=False) as db:
        with db.transaction():
            validate_company(company_id, user_id, db)
            records = db.execute(
                """SELECT id,contact_name,contact_email,contact_phone,service,
                          message,status,created_at
                   FROM cb.consultation_enquiries
                   WHERE company_id=%s
                   ORDER BY created_at DESC,id DESC LIMIT %s""",
                (company_id,limit),
            ).fetchall()
    return {"company_id":str(company_id),"enquiries":[{
        "id":str(r["id"]),"name":r["contact_name"],"email":r["contact_email"],
        "phone":r["contact_phone"],"service":r["service"],"message":r["message"],
        "status":r["status"],"created_at":r["created_at"].isoformat(),
    } for r in records]}


class ConsultationStatusChange(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: Literal["in_review", "responded", "closed"]


_ALLOWED = {
    "new": "in_review",
    "in_review": "responded",
    "responded": "closed",
}


@router.patch("/{enquiry_id}/status")
def update_consultation_status(
    company_id: UUID,
    enquiry_id: UUID,
    payload: ConsultationStatusChange,
    user_id: UUID = Depends(authenticate),
):
    """Director-only strict forward transitions; audit and update commit atomically."""
    _, _, _, dsn = config()
    with psycopg.connect(dsn, row_factory=dict_row, autocommit=False) as db:
        with db.transaction():
            validate_company(company_id, user_id, db)
            member = db.execute(
                "SELECT role FROM cb.memberships WHERE company_id=%s AND user_id=%s",
                (company_id, user_id),
            ).fetchone()
            if not member or member["role"] != "director":
                raise HTTPException(status_code=403, detail="Enquiry status changes require director access")
            record = db.execute(
                """SELECT status FROM cb.consultation_enquiries
                   WHERE company_id=%s AND id=%s FOR UPDATE""",
                (company_id, enquiry_id),
            ).fetchone()
            if record is None:
                raise HTTPException(status_code=404, detail="Enquiry not found")
            old = record["status"]
            if _ALLOWED.get(old) != payload.status:
                raise HTTPException(status_code=409, detail="Invalid enquiry status transition")
            db.execute(
                """UPDATE cb.consultation_enquiries
                   SET status=%s,updated_at=now()
                   WHERE company_id=%s AND id=%s""",
                (payload.status, company_id, enquiry_id),
            )
            db.execute(
                """INSERT INTO cb.consultation_status_audit
                   (company_id,enquiry_id,old_status,new_status,actor_id)
                   VALUES (%s,%s,%s,%s,%s)""",
                (company_id,enquiry_id,old,payload.status,user_id),
            )
    publish_consultation_change(company_id)
    return {"id":str(enquiry_id),"company_id":str(company_id),"status":payload.status}
