"""Read-only company-scoped client directory; no client creation endpoint yet."""
from __future__ import annotations

from uuid import UUID
import psycopg
from psycopg.rows import dict_row
from fastapi import APIRouter, Depends, Query

from api.main import authenticate, config, validate_company

router = APIRouter(prefix="/api/v1/companies/{company_id}/clients", tags=["clients"])

@router.get("")
def list_clients(
    company_id: UUID,
    limit: int = Query(default=50, ge=1, le=100),
    user_id: UUID = Depends(authenticate),
):
    _, _, _, dsn = config()
    with psycopg.connect(dsn, row_factory=dict_row, autocommit=False) as db:
        with db.transaction():
            validate_company(company_id, user_id, db)
            rows = db.execute(
                """SELECT id,client_code,legal_name,email,phone,status
                   FROM cb.clients WHERE company_id=%s
                   ORDER BY legal_name,id LIMIT %s""", (company_id, limit)
            ).fetchall()
    return {"company_id": str(company_id), "clients": [
        {"id": str(row["id"]), "code": row["client_code"],
         "name": row["legal_name"], "email": row["email"],
         "phone": row["phone"], "status": row["status"]}
        for row in rows
    ]}
