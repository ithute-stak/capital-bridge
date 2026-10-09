"""Transaction-safe server-side quotation transition and audit endpoint."""
from __future__ import annotations
from uuid import UUID
import psycopg
from psycopg.rows import dict_row
from pydantic import BaseModel, ConfigDict
from fastapi import APIRouter, Depends, HTTPException
from api.main import authenticate, config, validate_company
from api.quotation_approval_policy import validate_transition, QuotationTransitionError

router = APIRouter(prefix="/api/v1/companies/{company_id}/quotations", tags=["quotations"])

class TransitionPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    target_status: str

@router.post("/{quotation_id}/transition")
def transition_quotation(company_id: UUID, quotation_id: UUID,
                         payload: TransitionPayload, user_id: UUID = Depends(authenticate)):
    _, _, _, dsn = config()
    with psycopg.connect(dsn, row_factory=dict_row, autocommit=False) as db:
        with db.transaction():
            validate_company(company_id, user_id, db)
            membership = db.execute(
                "SELECT role FROM cb.memberships WHERE company_id=%s AND user_id=%s",
                (company_id, user_id),
            ).fetchone()
            if membership is None:
                raise HTTPException(status_code=403, detail="Company role required")
            quotation = db.execute(
                """SELECT status,subtotal_minor,issued_on,valid_until
                   FROM cb.quotations WHERE company_id=%s AND id=%s FOR UPDATE""",
                (company_id, quotation_id),
            ).fetchone()
            if quotation is None:
                raise HTTPException(status_code=404, detail="Quotation not found")
            totals = db.execute(
                """SELECT COUNT(*) AS line_count,
                   COALESCE(SUM(quantity * unit_price_minor),0) AS calculated_minor
                   FROM cb.quotation_lines WHERE company_id=%s AND quotation_id=%s""",
                (company_id, quotation_id),
            ).fetchone()
            try:
                decision = validate_transition(
                    quotation["status"], payload.target_status, membership["role"],
                    line_count=totals["line_count"],
                    subtotal_minor=quotation["subtotal_minor"],
                    calculated_minor=totals["calculated_minor"],
                    issued_on_present=quotation["issued_on"] is not None,
                    valid_until_present=quotation["valid_until"] is not None,
                )
            except QuotationTransitionError as exc:
                raise HTTPException(status_code=409, detail=str(exc)) from exc
            db.execute(
                "UPDATE cb.quotations SET status=%s WHERE company_id=%s AND id=%s",
                (decision.new_status, company_id, quotation_id),
            )
            db.execute(
                """INSERT INTO cb.quotation_status_events
                   (company_id,quotation_id,actor_user_id,from_status,to_status)
                   VALUES (%s,%s,%s,%s,%s)""",
                (company_id, quotation_id, user_id, decision.previous_status, decision.new_status),
            )
    return {"company_id": str(company_id), "quotation_id": str(quotation_id),
            "previous_status": decision.previous_status, "status": decision.new_status}
