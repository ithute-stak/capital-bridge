"""Company-authorized official receipt PDF delivery."""
from uuid import UUID
import psycopg
from psycopg.rows import dict_row
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from api.main import authenticate, config, validate_company
from api.quotation_download import trusted_logo
from api.receipt_pdf import OfficialReceipt, render_receipt_pdf

router=APIRouter(prefix="/api/v1/companies/{company_id}/receipts",tags=["receipts"])

@router.get("/{receipt_id}/pdf")
def receipt_pdf(company_id:UUID,receipt_id:UUID,user_id:UUID=Depends(authenticate)):
    _,_,_,dsn=config()
    with psycopg.connect(dsn,row_factory=dict_row,autocommit=False) as db:
        with db.transaction():
            validate_company(company_id,user_id,db)
            receipt=db.execute(
                """SELECT r.receipt_number,r.amount_minor,r.issued_at,p.paid_on,
                          p.payment_reference,p.method,p.status AS payment_status,
                          j.status AS journal_status,
                          c.legal_name AS company_name,cl.legal_name AS client_name
                   FROM cb.payment_receipts r
                   JOIN cb.client_payments p ON p.company_id=r.company_id AND p.id=r.payment_id
                   JOIN cb.journals j ON j.company_id=r.company_id AND j.id=r.journal_id
                   JOIN cb.companies c ON c.id=r.company_id
                   JOIN cb.clients cl ON cl.company_id=p.company_id AND cl.id=p.client_id
                   WHERE r.company_id=%s AND r.id=%s""",(company_id,receipt_id)).fetchone()
            if receipt is None:raise HTTPException(status_code=404,detail="Receipt not found")
            if receipt["payment_status"]!="verified" or receipt["journal_status"]!="posted":
                raise HTTPException(status_code=409,detail="Receipt accounting evidence unavailable")
            if receipt["amount_minor"]<=0:
                raise HTTPException(status_code=409,detail="Receipt financial amount invalid")
            item=OfficialReceipt(number=receipt["receipt_number"],company=receipt["company_name"],
                client=receipt["client_name"],payment_reference=receipt["payment_reference"],
                payment_date=receipt["paid_on"].isoformat(),issued_date=receipt["issued_at"].date().isoformat(),
                payment_method=receipt["method"],amount_minor=receipt["amount_minor"],
                currency="LSL",journal_status=receipt["journal_status"])
    try:
        pdf=render_receipt_pdf(item,approved_logo_path=trusted_logo())
    except (ValueError,RuntimeError,OSError) as exc:
        raise HTTPException(status_code=503,detail="Official receipt PDF unavailable") from exc
    return Response(pdf,media_type="application/pdf",headers={
        "Content-Disposition":f'attachment; filename="receipt-{receipt_id}.pdf"',
        "Cache-Control":"private, no-store","X-Content-Type-Options":"nosniff"})
