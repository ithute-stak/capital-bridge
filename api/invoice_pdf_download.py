"""Authenticated, company-isolated backend invoice PDF download."""
from __future__ import annotations
from uuid import UUID
import psycopg
from psycopg.rows import dict_row
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from api.main import authenticate, config, validate_company
from api.quotation_download import trusted_logo
from api.quotation_pdf import QuotationLine
from api.invoice_pdf import IssuedInvoice, render_issued_invoice_pdf

router=APIRouter(prefix="/api/v1/companies/{company_id}/invoices",tags=["invoices"])

@router.get("/{invoice_id}/pdf")
def invoice_pdf_download(company_id: UUID, invoice_id: UUID, user_id: UUID=Depends(authenticate)):
    _,_,_,dsn=config()
    with psycopg.connect(dsn,row_factory=dict_row,autocommit=False) as db:
        with db.transaction():
            validate_company(company_id,user_id,db)
            invoice=db.execute(
                """SELECT i.invoice_number,i.issued_on,i.due_on,i.status,i.currency,
                          i.subtotal_minor,i.tax_minor,c.legal_name AS company_name,
                          cl.legal_name AS client_name
                   FROM cb.invoices i
                   JOIN cb.companies c ON c.id=i.company_id
                   JOIN cb.clients cl ON cl.company_id=i.company_id AND cl.id=i.client_id
                   WHERE i.company_id=%s AND i.id=%s""",(company_id,invoice_id)
            ).fetchone()
            if invoice is None: raise HTTPException(status_code=404,detail="Invoice not found")
            if invoice["status"] not in ("issued","part_paid","paid"):
                raise HTTPException(status_code=409,detail="Only issued invoices are downloadable")
            lines=db.execute(
                """SELECT description,quantity,unit_price_minor FROM cb.invoice_lines
                   WHERE company_id=%s AND invoice_id=%s ORDER BY id""",
                (company_id,invoice_id)
            ).fetchall()
            if not lines or sum(x["quantity"]*x["unit_price_minor"] for x in lines)!=invoice["subtotal_minor"]:
                raise HTTPException(status_code=409,detail="Invoice totals require reconciliation")
            item=IssuedInvoice(
                reference=invoice["invoice_number"],company_name=invoice["company_name"],
                client_name=invoice["client_name"],issued_on=invoice["issued_on"].isoformat(),
                due_on=invoice["due_on"].isoformat(),currency=invoice["currency"].strip(),
                status=invoice["status"],subtotal_minor=invoice["subtotal_minor"],
                tax_minor=invoice["tax_minor"],lines=tuple(
                    QuotationLine(x["description"],x["quantity"],x["unit_price_minor"]) for x in lines))
    try: payload=render_issued_invoice_pdf(item,approved_logo_path=trusted_logo())
    except (ValueError,RuntimeError,OSError) as exc:
        raise HTTPException(status_code=503,detail="Official PDF publication unavailable") from exc
    return Response(payload,media_type="application/pdf",headers={
        "Content-Disposition":f'attachment; filename="invoice-{invoice_id}.pdf"',
        "Cache-Control":"private, no-store","X-Content-Type-Options":"nosniff"})
