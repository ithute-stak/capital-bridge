"""Authenticated server-side quotation PDF download, never browser rendering."""
from __future__ import annotations

import os
from pathlib import Path
from uuid import UUID

import psycopg
from psycopg.rows import dict_row
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response

from api.main import authenticate, config, validate_company
from api.quotation_pdf import ApprovedQuotation, QuotationLine, render_approved_quotation_pdf

router = APIRouter(prefix="/api/v1/companies/{company_id}/quotations", tags=["quotations"])


def trusted_logo() -> Path:
    # An operator-owned directory and an approved image filename; never HTTP input.
    logo = os.environ.get("CB_APPROVED_LOGO_PATH", "")
    path = Path(logo)
    if not logo or not path.is_absolute() or path.suffix.lower() not in {".png", ".jpg", ".jpeg"}:
        raise RuntimeError("Approved logo is not configured")
    return path


@router.get("/{quotation_id}/pdf")
def download_quotation(company_id: UUID, quotation_id: UUID, user_id: UUID = Depends(authenticate)):
    _, _, _, dsn = config()
    with psycopg.connect(dsn, row_factory=dict_row, autocommit=False) as db:
        with db.transaction():
            validate_company(company_id, user_id, db)
            row = db.execute(
                """SELECT q.quotation_number,q.status,q.currency,q.issued_on,q.valid_until,
                          q.subtotal_minor,q.tax_minor,c.legal_name AS company_name,
                          cl.legal_name AS client_name
                   FROM cb.quotations q
                   JOIN cb.companies c ON c.id=q.company_id
                   JOIN cb.clients cl ON cl.company_id=q.company_id AND cl.id=q.client_id
                   WHERE q.company_id=%s AND q.id=%s""",
                (company_id, quotation_id),
            ).fetchone()
            if row is None:
                raise HTTPException(status_code=404, detail="Quotation not found")
            if row["status"] not in ("approved", "sent", "accepted") or not row["issued_on"] or not row["valid_until"]:
                raise HTTPException(status_code=409, detail="Quotation is not approved for publication")
            lines = db.execute(
                """SELECT description,quantity,unit_price_minor
                   FROM cb.quotation_lines
                   WHERE company_id=%s AND quotation_id=%s ORDER BY id""",
                (company_id, quotation_id),
            ).fetchall()
            if not lines:
                raise HTTPException(status_code=409, detail="Quotation has no items")
            calculated = sum(line["quantity"] * line["unit_price_minor"] for line in lines)
            if calculated != row["subtotal_minor"]:
                raise HTTPException(status_code=409, detail="Quotation amounts require reconciliation")
            quotation = ApprovedQuotation(
                reference=row["quotation_number"], company_name=row["company_name"],
                client_name=row["client_name"], issued_on=row["issued_on"].isoformat(),
                valid_until=row["valid_until"].isoformat(), currency=row["currency"].strip(),
                status=row["status"], tax_minor=row["tax_minor"],
                lines=tuple(QuotationLine(line["description"], line["quantity"], line["unit_price_minor"]) for line in lines),
            )
    try:
        data = render_approved_quotation_pdf(quotation, approved_logo_path=trusted_logo())
    except (RuntimeError, ValueError, OSError) as exc:
        raise HTTPException(status_code=503, detail="Official PDF publication unavailable") from exc
    filename = f"quotation-{quotation_id}.pdf"
    return Response(
        content=data, media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "private, no-store",
            "X-Content-Type-Options": "nosniff",
        },
    )
