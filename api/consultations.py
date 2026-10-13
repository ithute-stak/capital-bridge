"""Authenticated, company-scoped consultation queue.

No public submission, no unauthenticated access, and no cross-company lookup.
Database runtime role must have explicit SELECT privileges and must not bypass RLS.
"""
from __future__ import annotations

from uuid import UUID
import psycopg
from psycopg.rows import dict_row
from fastapi import APIRouter, Depends, Query

from api.main import authenticate, config, validate_company

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
