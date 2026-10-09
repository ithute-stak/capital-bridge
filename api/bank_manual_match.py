"""Manual, auditable bank-to-payment reconciliation. Never marks a payment verified."""
from uuid import UUID,uuid4
import psycopg
from psycopg.rows import dict_row
from fastapi import APIRouter,Depends,HTTPException
from pydantic import BaseModel,ConfigDict
from api.main import authenticate,config,validate_company
from api.bank_reconciliation_policy import BankMatchEvidence,BankMatchError,validate_bank_payment_match

router=APIRouter(prefix="/api/v1/companies/{company_id}/bank",tags=["bank"])

class MatchBankTransaction(BaseModel):
    model_config=ConfigDict(extra="forbid")
    payment_id: UUID

@router.post("/transactions/{transaction_id}/match")
def match_bank_transaction(company_id:UUID,transaction_id:UUID,payload:MatchBankTransaction,
                           user_id:UUID=Depends(authenticate)):
    _,_,_,dsn=config()
    match_id=uuid4()
    with psycopg.connect(dsn,row_factory=dict_row,autocommit=False) as db:
        with db.transaction():
            validate_company(company_id,user_id,db)
            member=db.execute("SELECT role FROM cb.memberships WHERE company_id=%s AND user_id=%s",
                              (company_id,user_id)).fetchone()
            if not member or member["role"] not in {"director","accountant"}:
                raise HTTPException(status_code=403,detail="Bank reconciliation denied")
            # Company lock serialises competing matches to separate transactions.
            db.execute("SELECT id FROM cb.companies WHERE id=%s FOR UPDATE",(company_id,))
            transaction=db.execute(
                """SELECT amount_minor,currency,description,transaction_date
                   FROM cb.bank_statement_transactions WHERE company_id=%s AND id=%s FOR UPDATE""",
                (company_id,transaction_id)).fetchone()
            payment=db.execute(
                """SELECT amount_minor,currency,payment_reference,paid_on,status
                   FROM cb.client_payments WHERE company_id=%s AND id=%s FOR UPDATE""",
                (company_id,payload.payment_id)).fetchone()
            if transaction is None or payment is None:
                raise HTTPException(status_code=404,detail="Bank transaction or payment not found")
            try:
                validate_bank_payment_match(BankMatchEvidence(
                    bank_amount_minor=transaction["amount_minor"],payment_amount_minor=payment["amount_minor"],
                    payment_status=payment["status"],bank_currency=transaction["currency"].strip(),
                    payment_currency=payment["currency"].strip(),company_matches=True,
                    payment_reference=payment["payment_reference"],
                    bank_description=transaction["description"],
                    bank_date=transaction["transaction_date"],payment_date=payment["paid_on"],
                    actor_role=member["role"]))
            except BankMatchError as exc:
                raise HTTPException(status_code=409,detail=str(exc)) from exc
            if db.execute("""SELECT id FROM cb.bank_payment_matches
                WHERE company_id=%s AND (bank_transaction_id=%s OR payment_id=%s)""",
                (company_id,transaction_id,payload.payment_id)).fetchone():
                raise HTTPException(status_code=409,detail="Bank transaction or payment already matched")
            db.execute("""INSERT INTO cb.bank_payment_matches
                (id,company_id,bank_transaction_id,payment_id,matched_by)
                VALUES (%s,%s,%s,%s,%s)""",
                (match_id,company_id,transaction_id,payload.payment_id,user_id))
            db.execute("""UPDATE cb.bank_import_exceptions SET status='resolved',
                resolved_by=%s,resolved_at=now(),notes='Matched to verified payment'
                WHERE company_id=%s AND bank_transaction_id=%s AND status IN ('open','investigating')""",
                (user_id,company_id,transaction_id))
    return {"id":str(match_id),"company_id":str(company_id),
            "bank_transaction_id":str(transaction_id),"payment_id":str(payload.payment_id),
            "matched_by":str(user_id),"status":"matched"}
