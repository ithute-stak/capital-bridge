"""Create a draft invoice from a previously accepted quotation.

Only database-resident items and computed integer amounts are trusted.
"""
from __future__ import annotations
from datetime import date
from uuid import UUID, uuid4
import psycopg
from psycopg.rows import dict_row
from pydantic import BaseModel, ConfigDict, Field, model_validator
from fastapi import APIRouter, Depends, HTTPException, status
from api.main import authenticate, config, validate_company

router = APIRouter(prefix="/api/v1/companies/{company_id}/invoices", tags=["invoices"])

class InvoiceFromQuotation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    quotation_id: UUID
    invoice_number: str = Field(min_length=1, max_length=60)
    issued_on: date
    due_on: date

    @model_validator(mode="after")
    def valid_reference_and_dates(self):
        if not self.invoice_number.strip() or self.due_on < self.issued_on:
            raise ValueError("Valid invoice reference and due date required")
        return self

@router.post("/from-quotation", status_code=status.HTTP_201_CREATED)
def create_invoice_from_quotation(company_id: UUID, payload: InvoiceFromQuotation,
                                  user_id: UUID = Depends(authenticate)):
    _, _, _, dsn = config()
    invoice_id = uuid4()
    with psycopg.connect(dsn, row_factory=dict_row, autocommit=False) as db:
        with db.transaction():
            validate_company(company_id, user_id, db)
            role = db.execute(
                "SELECT role FROM cb.memberships WHERE company_id=%s AND user_id=%s",
                (company_id, user_id),
            ).fetchone()
            if not role or role["role"] not in {"director", "accountant"}:
                raise HTTPException(status_code=403, detail="Invoice creation denied")
            quotation = db.execute(
                """SELECT id,client_id,currency,status,subtotal_minor,tax_minor
                   FROM cb.quotations WHERE company_id=%s AND id=%s FOR UPDATE""",
                (company_id, payload.quotation_id),
            ).fetchone()
            if quotation is None:
                raise HTTPException(status_code=404, detail="Quotation not found")
            if quotation["status"] != "accepted" or quotation["currency"].strip() != "LSL":
                raise HTTPException(status_code=409, detail="Accepted LSL quotation required")
            lines = db.execute(
                """SELECT description,quantity,unit_price_minor
                   FROM cb.quotation_lines WHERE company_id=%s AND quotation_id=%s ORDER BY id""",
                (company_id, payload.quotation_id),
            ).fetchall()
            subtotal = sum(x["quantity"] * x["unit_price_minor"] for x in lines)
            if not lines or subtotal != quotation["subtotal_minor"]:
                raise HTTPException(status_code=409, detail="Quotation totals are inconsistent")
            if not 0 <= quotation["tax_minor"] <= 9223372036854775807 - subtotal:
                raise HTTPException(status_code=409, detail="Quotation tax amount is invalid")
            # Prevent accidental duplicate invoices from the same quotation.
            existing = db.execute(
                "SELECT id FROM cb.invoices WHERE company_id=%s AND quotation_id=%s",
                (company_id, payload.quotation_id),
            ).fetchone()
            if existing:
                raise HTTPException(status_code=409, detail="Quotation is already invoiced")
            try:
                db.execute(
                    """INSERT INTO cb.invoices
                       (id,company_id,client_id,quotation_id,invoice_number,issued_on,
                        due_on,currency,status,subtotal_minor,tax_minor)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,'LSL','draft',%s,%s)""",
                    (invoice_id, company_id, quotation["client_id"],payload.quotation_id,
                     payload.invoice_number.strip(), payload.issued_on,payload.due_on,
                     subtotal,quotation["tax_minor"]),
                )
                for line in lines:
                    db.execute(
                        """INSERT INTO cb.invoice_lines
                           (company_id,invoice_id,description,quantity,unit_price_minor)
                           VALUES (%s,%s,%s,%s,%s)""",
                        (company_id,invoice_id,line["description"],
                         line["quantity"],line["unit_price_minor"]),
                    )
            except psycopg.errors.UniqueViolation as exc:
                raise HTTPException(status_code=409,detail="Invoice already exists") from exc
    return {"id":str(invoice_id),"company_id":str(company_id),"quotation_id":str(payload.quotation_id),
            "status":"draft","currency":"LSL","subtotal_minor":subtotal,
            "tax_minor":quotation["tax_minor"],"total_minor":subtotal + quotation["tax_minor"]}
