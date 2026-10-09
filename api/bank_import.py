"""Safe bank statement ingestion: records evidence, never auto-matches funds."""
from __future__ import annotations
from datetime import date
from uuid import UUID,uuid4
import psycopg
from psycopg.rows import dict_row
from fastapi import APIRouter,Depends,HTTPException,status
from pydantic import BaseModel,ConfigDict,Field,model_validator
from api.main import authenticate,config,validate_company

router=APIRouter(prefix="/api/v1/companies/{company_id}/bank",tags=["bank"])

class BankStatementRow(BaseModel):
    model_config=ConfigDict(extra="forbid")
    account_reference: str=Field(min_length=1,max_length=80)
    transaction_reference: str=Field(min_length=1,max_length=160)
    transaction_date: date
    description: str=Field(default="",max_length=1500)
    amount_minor: int=Field(ge=-9223372036854775807,le=9223372036854775807)
    currency: str=Field(pattern="^LSL$")
    @model_validator(mode="after")
    def nonzero_amount(self):
        if not self.amount_minor or not self.account_reference.strip() or not self.transaction_reference.strip():
            raise ValueError("Nonzero bank transaction and references required")
        return self

class BankImportRequest(BaseModel):
    model_config=ConfigDict(extra="forbid")
    rows: list[BankStatementRow]=Field(min_length=1,max_length=500)

@router.post("/statement-imports",status_code=status.HTTP_201_CREATED)
def import_bank_rows(company_id:UUID,payload:BankImportRequest,user_id:UUID=Depends(authenticate)):
    _,_,_,dsn=config()
    imported=[]
    with psycopg.connect(dsn,row_factory=dict_row,autocommit=False) as db:
        with db.transaction():
            validate_company(company_id,user_id,db)
            member=db.execute("SELECT role FROM cb.memberships WHERE company_id=%s AND user_id=%s",
                              (company_id,user_id)).fetchone()
            if not member or member["role"] not in {"director","accountant"}:
                raise HTTPException(status_code=403,detail="Bank statement import denied")
            keys=[(row.account_reference.strip(),row.transaction_reference.strip()) for row in payload.rows]
            if len(keys)!=len(set(keys)):
                raise HTTPException(status_code=409,detail="Duplicate statement rows in import")
            for row in payload.rows:
                transaction_id=uuid4()
                try:
                    db.execute("""INSERT INTO cb.bank_statement_transactions
                        (id,company_id,bank_account_ref,external_transaction_id,
                         transaction_date,description,amount_minor,currency)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,'LSL')""",
                        (transaction_id,company_id,row.account_reference.strip(),
                         row.transaction_reference.strip(),row.transaction_date,
                         row.description,row.amount_minor))
                except psycopg.errors.UniqueViolation as exc:
                    raise HTTPException(status_code=409,detail="Bank transaction already imported") from exc
                db.execute("""INSERT INTO cb.bank_import_exceptions
                    (id,company_id,bank_transaction_id,reason,status)
                    VALUES (%s,%s,%s,'unmatched','open')""",
                    (uuid4(),company_id,transaction_id))
                imported.append(str(transaction_id))
    return {"company_id":str(company_id),"imported":len(imported),
            "bank_transaction_ids":imported,"review_required":len(imported),
            "automatic_matches":0}
