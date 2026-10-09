"""Read-only company-scoped client directory; no client creation endpoint yet."""
from __future__ import annotations

from uuid import UUID, uuid4
import psycopg
from psycopg.rows import dict_row
from fastapi import APIRouter, Depends, Query, HTTPException, status

from api.main import authenticate, config, validate_company
from api.client_schemas import ClientCreate
from api.client_update_schema import ClientUpdate
from api.finance_outbox import enqueue_finance_event

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


@router.post("", status_code=status.HTTP_201_CREATED)
def create_client(
    company_id: UUID,
    payload: ClientCreate,
    user_id: UUID = Depends(authenticate),
):
    """Only directors, accountants and finance clerks can create CRM records."""
    _, _, _, dsn = config()
    client_id = uuid4()
    with psycopg.connect(dsn, row_factory=dict_row, autocommit=False) as db:
        with db.transaction():
            validate_company(company_id, user_id, db)
            role = db.execute(
                "SELECT role FROM cb.memberships WHERE company_id=%s AND user_id=%s",
                (company_id, user_id),
            ).fetchone()
            if not role or role["role"] not in ("director", "accountant", "finance_clerk"):
                raise HTTPException(status_code=403, detail="Client creation denied")
            try:
                db.execute(
                    """INSERT INTO cb.clients
                       (id, company_id, client_code, legal_name, email, phone)
                       VALUES (%s,%s,%s,%s,%s,%s)""",
                    (client_id, company_id, payload.client_code, payload.legal_name,
                     payload.email, payload.phone),
                )
                enqueue_finance_event(db,company_id=company_id,event_type="client.created",
                                      aggregate_id=client_id)
            except psycopg.errors.UniqueViolation as exc:
                raise HTTPException(status_code=409, detail="Client code already exists") from exc
    return {"id": str(client_id), "company_id": str(company_id), "code": payload.client_code,
            "name": payload.legal_name, "status": "active"}


@router.put("/{client_id}")
def update_client(
    company_id: UUID,
    client_id: UUID,
    payload: ClientUpdate,
    user_id: UUID = Depends(authenticate),
):
    """Edit permitted CRM details; never change immutable ownership or reference."""
    _, _, _, dsn = config()
    with psycopg.connect(dsn, row_factory=dict_row, autocommit=False) as db:
        with db.transaction():
            validate_company(company_id, user_id, db)
            role = db.execute(
                "SELECT role FROM cb.memberships WHERE company_id=%s AND user_id=%s",
                (company_id, user_id),
            ).fetchone()
            if not role or role["role"] not in ("director", "accountant", "finance_clerk"):
                raise HTTPException(status_code=403, detail="Client editing denied")
            result = db.execute(
                """UPDATE cb.clients SET legal_name=%s, email=%s, phone=%s, status=%s
                   WHERE company_id=%s AND id=%s
                   RETURNING client_code""",
                (payload.legal_name, payload.email, payload.phone, payload.status,
                 company_id, client_id),
            ).fetchone()
            if result is None:
                raise HTTPException(status_code=404, detail="Client not found")
            enqueue_finance_event(db,company_id=company_id,event_type="client.updated",
                                  aggregate_id=client_id)
    return {"id": str(client_id), "company_id": str(company_id),
            "code": result["client_code"], "name": payload.legal_name,
            "status": payload.status}
