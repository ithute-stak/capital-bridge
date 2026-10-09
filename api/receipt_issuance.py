"""Issue an official receipt only for a verified payment and posted cash journal."""
from uuid import UUID,uuid4
import psycopg
from psycopg.rows import dict_row
from fastapi import APIRouter,Depends,HTTPException,status
from pydantic import BaseModel,ConfigDict,Field
from api.main import authenticate,config,validate_company
from api.receipt_publication_policy import ReceiptEvidence,ReceiptPublicationError,validate_receipt_evidence

router=APIRouter(prefix="/api/v1/companies/{company_id}/receipts",tags=["receipts"])

class IssueReceipt(BaseModel):
    model_config=ConfigDict(extra="forbid")
    payment_id: UUID
    journal_id: UUID
    receipt_number: str=Field(min_length=1,max_length=80)

@router.post("",status_code=status.HTTP_201_CREATED)
def issue_receipt(company_id:UUID,payload:IssueReceipt,user_id:UUID=Depends(authenticate)):
    _,_,_,dsn=config()
    receipt_id=uuid4()
    with psycopg.connect(dsn,row_factory=dict_row,autocommit=False) as db:
        with db.transaction():
            validate_company(company_id,user_id,db)
            member=db.execute("SELECT role FROM cb.memberships WHERE company_id=%s AND user_id=%s",
                              (company_id,user_id)).fetchone()
            payment=db.execute("SELECT id,amount_minor,status FROM cb.client_payments WHERE company_id=%s AND id=%s FOR UPDATE",
                               (company_id,payload.payment_id)).fetchone()
            journal=db.execute("SELECT id,status,reference FROM cb.journals WHERE company_id=%s AND id=%s FOR UPDATE",
                               (company_id,payload.journal_id)).fetchone()
            if not payment or not journal:
                raise HTTPException(status_code=404,detail="Payment or accounting journal not found")
            if journal["reference"]!="PAY:"+str(payload.payment_id):
                raise HTTPException(status_code=409,detail="Accounting journal does not correspond to payment")
            try:
                validate_receipt_evidence(ReceiptEvidence(
                    payment_minor=payment["amount_minor"],receipt_minor=payment["amount_minor"],
                    payment_status=payment["status"],journal_status=journal["status"],
                    payment_company_matches=True,journal_company_matches=True,
                    actor_role=member["role"] if member else ""))
            except ReceiptPublicationError as exc:
                raise HTTPException(status_code=409,detail=str(exc)) from exc
            existing=db.execute("SELECT id FROM cb.payment_receipts WHERE company_id=%s AND payment_id=%s",
                                (company_id,payload.payment_id)).fetchone()
            if existing:
                raise HTTPException(status_code=409,detail="Payment has already been receipted")
            try:
                db.execute("""INSERT INTO cb.payment_receipts
                    (id,company_id,payment_id,journal_id,receipt_number,amount_minor,issued_by)
                    VALUES (%s,%s,%s,%s,%s,%s,%s)""",
                    (receipt_id,company_id,payload.payment_id,payload.journal_id,
                     payload.receipt_number.strip(),payment["amount_minor"],user_id))
            except psycopg.errors.UniqueViolation as exc:
                raise HTTPException(status_code=409,detail="Receipt already exists") from exc
    return {"id":str(receipt_id),"company_id":str(company_id),
            "payment_id":str(payload.payment_id),"receipt_number":payload.receipt_number.strip(),
            "amount_minor":payment["amount_minor"],"status":"issued"}
