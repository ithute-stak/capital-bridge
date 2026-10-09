"""Atomic invoice issuance into an immutable posted journal; backend only."""
from __future__ import annotations
from uuid import UUID,uuid4
import psycopg
from psycopg.rows import dict_row
from fastapi import APIRouter,Depends,HTTPException
from pydantic import BaseModel,ConfigDict
from api.main import authenticate,config,validate_company
from api.invoice_posting_policy import validate_invoice_posting,InvoicePostingError

router=APIRouter(prefix="/api/v1/companies/{company_id}/invoices",tags=["invoices"])
class IssueInvoice(BaseModel):
    model_config=ConfigDict(extra="forbid")
    period_id: UUID
    receivable_account: str
    revenue_account: str
    tax_account: str | None = None
    division: str

@router.post("/{invoice_id}/issue")
def issue_invoice(company_id:UUID,invoice_id:UUID,payload:IssueInvoice,user_id:UUID=Depends(authenticate)):
    _,_,_,dsn=config()
    journal_id=uuid4()
    with psycopg.connect(dsn,row_factory=dict_row,autocommit=False) as db:
        with db.transaction():
            validate_company(company_id,user_id,db)
            member=db.execute("SELECT role FROM cb.memberships WHERE company_id=%s AND user_id=%s",(company_id,user_id)).fetchone()
            invoice=db.execute("SELECT id,issued_on,status,subtotal_minor,tax_minor FROM cb.invoices WHERE company_id=%s AND id=%s FOR UPDATE",(company_id,invoice_id)).fetchone()
            if invoice is None: raise HTTPException(status_code=404,detail="Invoice not found")
            period=db.execute("SELECT starts_on,ends_on,closed FROM cb.periods WHERE company_id=%s AND id=%s FOR UPDATE",(company_id,payload.period_id)).fetchone()
            totals=db.execute("SELECT COUNT(*) AS n,COALESCE(SUM(quantity*unit_price_minor),0) AS subtotal FROM cb.invoice_lines WHERE company_id=%s AND invoice_id=%s",(company_id,invoice_id)).fetchone()
            accounts=[payload.receivable_account,payload.revenue_account]+([payload.tax_account] if invoice["tax_minor"] else [])
            if not all(accounts) or len(set(accounts))!=len(accounts):
                raise HTTPException(status_code=409,detail="Distinct financial accounts required")
            active=db.execute("SELECT code,kind FROM cb.accounts WHERE company_id=%s AND code=ANY(%s) AND active=true",(company_id,accounts)).fetchall()
            kinds={row["code"]:row["kind"] for row in active}
            try:
                decision=validate_invoice_posting(
                    actor_role=member["role"] if member else "",
                    invoice_status=invoice["status"],
                    period_open=bool(period and not period["closed"]),
                    date_in_period=bool(period and period["starts_on"]<=invoice["issued_on"]<=period["ends_on"]),
                    line_count=totals["n"],subtotal_minor=invoice["subtotal_minor"],
                    calculated_subtotal_minor=totals["subtotal"],tax_minor=invoice["tax_minor"],
                    receivable_account_active=kinds.get(payload.receivable_account)=="asset",
                    revenue_account_active=kinds.get(payload.revenue_account)=="revenue",
                    tax_account_active=not invoice["tax_minor"] or kinds.get(payload.tax_account)=="liability")
            except InvoicePostingError as exc:
                raise HTTPException(status_code=409,detail=str(exc)) from exc
            db.execute("""INSERT INTO cb.journals(id,company_id,period_id,posted_on,reference,description,status)
                       VALUES (%s,%s,%s,%s,%s,%s,'draft')""",
                       (journal_id,company_id,payload.period_id,invoice["issued_on"],"INV:"+str(invoice_id),"Invoice issuance"))
            entries=[(payload.receivable_account,decision.receivable_debit_minor,0),
                     (payload.revenue_account,0,decision.revenue_credit_minor)]
            if decision.tax_credit_minor:
                entries.append((payload.tax_account,0,decision.tax_credit_minor))
            for account,debit,credit in entries:
                db.execute("""INSERT INTO cb.journal_lines(company_id,journal_id,account_code,division,debit_minor,credit_minor)
                           VALUES (%s,%s,%s,%s,%s,%s)""",(company_id,journal_id,account,payload.division,debit,credit))
            db.execute("UPDATE cb.journals SET status='posted' WHERE company_id=%s AND id=%s",(company_id,journal_id))
            db.execute("UPDATE cb.invoices SET status='issued' WHERE company_id=%s AND id=%s AND status='draft'",(company_id,invoice_id))
    return {"company_id":str(company_id),"invoice_id":str(invoice_id),"journal_id":str(journal_id),"status":"issued"}
