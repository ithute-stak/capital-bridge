"""Company-scoped atomic allocation of a verified payment to an issued invoice."""
from uuid import UUID, uuid4
import psycopg
from psycopg.rows import dict_row
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from api.main import authenticate, config, validate_company
from api.payment_allocation_policy import validate_allocation, AllocationError

router = APIRouter(prefix="/api/v1/companies/{company_id}/payments", tags=["payments"])

class AllocatePayment(BaseModel):
    model_config = ConfigDict(extra="forbid")
    invoice_id: UUID
    amount_minor: int = Field(gt=0, le=9223372036854775807)

@router.post("/{payment_id}/allocate")
def allocate_payment(company_id: UUID, payment_id: UUID, payload: AllocatePayment,
                     user_id: UUID = Depends(authenticate)):
    _, _, _, dsn = config()
    allocation_id = uuid4()
    with psycopg.connect(dsn, row_factory=dict_row, autocommit=False) as db:
        with db.transaction():
            validate_company(company_id, user_id, db)
            role = db.execute("SELECT role FROM cb.memberships WHERE company_id=%s AND user_id=%s",
                              (company_id, user_id)).fetchone()
            if not role or role["role"] not in {"director", "accountant"}:
                raise HTTPException(status_code=403, detail="Payment allocation denied")
            # Serialise company allocations through a single row lock, ensuring that
            # different payments cannot over-allocate one invoice concurrently.
            db.execute("SELECT id FROM cb.companies WHERE id=%s FOR UPDATE", (company_id,))
            payment = db.execute(
                "SELECT client_id,status,amount_minor FROM cb.client_payments WHERE company_id=%s AND id=%s FOR UPDATE",
                (company_id, payment_id)).fetchone()
            invoice = db.execute(
                """SELECT client_id,status,total_minor FROM cb.invoices
                   WHERE company_id=%s AND id=%s FOR UPDATE""",
                (company_id, payload.invoice_id)).fetchone()
            if payment is None or invoice is None:
                raise HTTPException(status_code=404, detail="Payment or invoice not found")
            paid = db.execute(
                """SELECT COALESCE(SUM(amount_minor),0) AS allocated FROM cb.payment_allocations
                   WHERE company_id=%s AND payment_id=%s""", (company_id, payment_id)).fetchone()
            allocated = db.execute(
                """SELECT COALESCE(SUM(amount_minor),0) AS allocated FROM cb.payment_allocations
                   WHERE company_id=%s AND invoice_id=%s""", (company_id, payload.invoice_id)).fetchone()
            try:
                _, remaining = validate_allocation(
                    payment_status=payment["status"], payment_minor=payment["amount_minor"],
                    previously_allocated_minor=paid["allocated"], proposed_minor=payload.amount_minor,
                    invoice_status=invoice["status"], invoice_total_minor=invoice["total_minor"],
                    invoice_allocated_minor=allocated["allocated"], same_company=True,
                    same_client=payment["client_id"] == invoice["client_id"])
            except AllocationError as exc:
                raise HTTPException(status_code=409, detail=str(exc)) from exc
            db.execute(
                """INSERT INTO cb.payment_allocations(id,company_id,payment_id,invoice_id,amount_minor)
                   VALUES (%s,%s,%s,%s,%s)""",
                (allocation_id, company_id, payment_id, payload.invoice_id, payload.amount_minor))
            db.execute(
                "UPDATE cb.invoices SET status=%s WHERE company_id=%s AND id=%s",
                ("paid" if remaining == 0 else "part_paid", company_id, payload.invoice_id))
    return {"id": str(allocation_id), "company_id": str(company_id),
            "payment_id": str(payment_id), "invoice_id": str(payload.invoice_id),
            "allocated_minor": payload.amount_minor,
            "outstanding_minor": remaining, "invoice_status": "paid" if remaining == 0 else "part_paid"}
