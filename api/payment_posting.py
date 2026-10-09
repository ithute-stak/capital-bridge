"""Post a verified payment to cash/bank and receivables in one DB transaction."""
from uuid import UUID,uuid4
import psycopg
from psycopg.rows import dict_row
from fastapi import APIRouter,Depends,HTTPException
from pydantic import BaseModel,ConfigDict,Field
from api.main import authenticate,config,validate_company

router=APIRouter(prefix="/api/v1/companies/{company_id}/payments",tags=["payments"])

class PostPayment(BaseModel):
    model_config=ConfigDict(extra="forbid")
    period_id: UUID
    deposit_account: str=Field(min_length=1,max_length=40)
    receivable_account: str=Field(min_length=1,max_length=40)
    division: str=Field(min_length=1,max_length=80)

@router.post("/{payment_id}/post")
def post_payment(company_id:UUID,payment_id:UUID,payload:PostPayment,user_id:UUID=Depends(authenticate)):
    _,_,_,dsn=config()
    journal_id=uuid4()
    with psycopg.connect(dsn,row_factory=dict_row,autocommit=False) as db:
        with db.transaction():
            validate_company(company_id,user_id,db)
            member=db.execute("SELECT role FROM cb.memberships WHERE company_id=%s AND user_id=%s",
                              (company_id,user_id)).fetchone()
            if not member or member["role"] not in {"director","accountant"}:
                raise HTTPException(status_code=403,detail="Payment posting denied")
            payment=db.execute(
                "SELECT paid_on,amount_minor,status FROM cb.client_payments WHERE company_id=%s AND id=%s FOR UPDATE",
                (company_id,payment_id)).fetchone()
            if payment is None: raise HTTPException(status_code=404,detail="Payment not found")
            if payment["status"]!="verified" or payment["amount_minor"]<=0:
                raise HTTPException(status_code=409,detail="Verified positive payment required")
            existing=db.execute("SELECT id FROM cb.journals WHERE company_id=%s AND reference=%s",
                                (company_id,"PAY:"+str(payment_id))).fetchone()
            if existing: raise HTTPException(status_code=409,detail="Payment already posted")
            period=db.execute("SELECT starts_on,ends_on,closed FROM cb.periods WHERE company_id=%s AND id=%s FOR UPDATE",
                              (company_id,payload.period_id)).fetchone()
            if not period or period["closed"] or not(period["starts_on"]<=payment["paid_on"]<=period["ends_on"]):
                raise HTTPException(status_code=409,detail="Open accounting period required")
            if payload.deposit_account==payload.receivable_account:
                raise HTTPException(status_code=409,detail="Distinct ledger accounts required")
            accounts=db.execute("SELECT code,kind FROM cb.accounts WHERE company_id=%s AND code=ANY(%s) AND active=true",
                                (company_id,[payload.deposit_account,payload.receivable_account])).fetchall()
            kinds={x["code"]:x["kind"] for x in accounts}
            if kinds.get(payload.deposit_account)!="asset" or kinds.get(payload.receivable_account)!="asset":
                raise HTTPException(status_code=409,detail="Active asset ledger accounts required")
            db.execute("""INSERT INTO cb.journals(id,company_id,period_id,posted_on,reference,description,status)
                       VALUES (%s,%s,%s,%s,%s,%s,'draft')""",
                       (journal_id,company_id,payload.period_id,payment["paid_on"],
                        "PAY:"+str(payment_id),"Verified payment received"))
            for code,debit,credit in (
                (payload.deposit_account,payment["amount_minor"],0),
                (payload.receivable_account,0,payment["amount_minor"])):
                db.execute("""INSERT INTO cb.journal_lines(company_id,journal_id,account_code,division,debit_minor,credit_minor)
                           VALUES (%s,%s,%s,%s,%s,%s)""",
                           (company_id,journal_id,code,payload.division,debit,credit))
            db.execute("UPDATE cb.journals SET status='posted' WHERE company_id=%s AND id=%s",
                       (company_id,journal_id))
    return {"company_id":str(company_id),"payment_id":str(payment_id),
            "journal_id":str(journal_id),"status":"posted"}
