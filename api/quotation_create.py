"""Create draft quotations and lines atomically on the backend."""
from __future__ import annotations
from uuid import UUID, uuid4
import psycopg
from psycopg.rows import dict_row
from fastapi import APIRouter, Depends, HTTPException, status
from api.main import authenticate, config, validate_company
from api.quotation_create_schema import QuotationCreateInput

router = APIRouter(prefix="/api/v1/companies/{company_id}/quotations", tags=["quotations"])

@router.post("", status_code=status.HTTP_201_CREATED)
def create_quotation(company_id: UUID, payload: QuotationCreateInput,
                     user_id: UUID = Depends(authenticate)):
    _, _, _, dsn = config()
    quote_id = uuid4()
    with psycopg.connect(dsn, row_factory=dict_row, autocommit=False) as db:
        with db.transaction():
            validate_company(company_id, user_id, db)
            role = db.execute(
                "SELECT role FROM cb.memberships WHERE company_id=%s AND user_id=%s",
                (company_id, user_id),
            ).fetchone()
            if role is None or role["role"] not in {"director","accountant","finance_clerk"}:
                raise HTTPException(status_code=403, detail="Quotation creation denied")
            client = db.execute(
                "SELECT id FROM cb.clients WHERE company_id=%s AND id=%s AND status='active'",
                (company_id, payload.client_id),
            ).fetchone()
            if client is None:
                raise HTTPException(status_code=404, detail="Active client not found")
            try:
                db.execute(
                    """INSERT INTO cb.quotations
                       (id,company_id,client_id,quotation_number,title,currency,status,
                        issued_on,valid_until,subtotal_minor,tax_minor)
                       VALUES (%s,%s,%s,%s,%s,'LSL','draft',%s,%s,%s,0)""",
                    (quote_id, company_id, payload.client_id, payload.quotation_number.strip(),
                     payload.title.strip(), payload.issued_on, payload.valid_until,
                     payload.subtotal_minor),
                )
                for line in payload.lines:
                    db.execute(
                        """INSERT INTO cb.quotation_lines
                           (company_id,quotation_id,description,quantity,unit_price_minor)
                           VALUES (%s,%s,%s,%s,%s)""",
                        (company_id, quote_id, line.description.strip(), line.quantity,
                         line.unit_price_minor),
                    )
            except psycopg.errors.UniqueViolation as exc:
                raise HTTPException(status_code=409, detail="Quotation reference already exists") from exc
    return {"id": str(quote_id), "company_id": str(company_id), "status": "draft",
            "quotation_number": payload.quotation_number.strip(),
            "currency": "LSL", "subtotal_minor": payload.subtotal_minor,
            "tax_minor": 0, "total_minor": payload.subtotal_minor}
