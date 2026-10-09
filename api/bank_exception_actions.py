"""Authenticated exception investigation with immutable action history."""
from uuid import UUID
import psycopg
from psycopg.rows import dict_row
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from typing import Literal
from api.main import authenticate, config, validate_company

router=APIRouter(prefix="/api/v1/companies/{company_id}/bank",tags=["bank"])

class ExceptionAction(BaseModel):
    model_config=ConfigDict(extra="forbid")
    status: Literal["investigating","resolved"]
    note: str=Field(min_length=8,max_length=2000)

@router.post("/exceptions/{exception_id}/actions")
def update_bank_exception(company_id:UUID,exception_id:UUID,payload:ExceptionAction,
                          user_id:UUID=Depends(authenticate)):
    _,_,_,dsn=config()
    with psycopg.connect(dsn,row_factory=dict_row,autocommit=False) as db:
        with db.transaction():
            validate_company(company_id,user_id,db)
            member=db.execute("SELECT role FROM cb.memberships WHERE company_id=%s AND user_id=%s",
                              (company_id,user_id)).fetchone()
            if not member or member["role"] not in {"director","accountant"}:
                raise HTTPException(status_code=403,detail="Bank exception review denied")
            row=db.execute("SELECT status FROM cb.bank_import_exceptions WHERE company_id=%s AND id=%s FOR UPDATE",
                           (company_id,exception_id)).fetchone()
            if not row:raise HTTPException(status_code=404,detail="Bank exception not found")
            if row["status"]=="resolved" or row["status"]==payload.status:
                raise HTTPException(status_code=409,detail="Invalid exception status transition")
            if row["status"]=="open" and payload.status!="investigating":
                raise HTTPException(status_code=409,detail="Investigation required before resolution")
            note=payload.note.strip()
            if len(note)<8:raise HTTPException(status_code=422,detail="Investigation note required")
            db.execute("""INSERT INTO cb.bank_exception_actions
                (company_id,exception_id,actor_user_id,from_status,to_status,action_note)
                VALUES (%s,%s,%s,%s,%s,%s)""",
                (company_id,exception_id,user_id,row["status"],payload.status,note))
            db.execute("""UPDATE cb.bank_import_exceptions SET status=%s,notes=%s,
                resolved_by=CASE WHEN %s='resolved' THEN %s ELSE NULL END,
                resolved_at=CASE WHEN %s='resolved' THEN now() ELSE NULL END
                WHERE company_id=%s AND id=%s""",
                (payload.status,note,payload.status,user_id,payload.status,company_id,exception_id))
    return {"company_id":str(company_id),"exception_id":str(exception_id),
            "status":payload.status,"reviewed_by":str(user_id)}
