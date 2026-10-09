"""Authenticated, read-only finance API backed by PostgreSQL.

OIDC tokens are cryptographically verified against configured JWKS. Caller-provided
company identifiers are never treated as proof of membership. All SQL runs within
a transaction with transaction-local RLS context.
"""
from __future__ import annotations

import os
from datetime import date
from uuid import UUID

import jwt
import psycopg
from fastapi import Depends, FastAPI, Header, HTTPException, Query
from jwt import PyJWKClient
from psycopg.rows import dict_row
from api.finance_authorization import require_company_membership

app = FastAPI(title="CapitalBridge ONE Finance API", version="0.1.0")


def config() -> tuple[str, str, str, str]:
    issuer = os.environ.get("CB_OIDC_ISSUER", "").rstrip("/")
    audience = os.environ.get("CB_OIDC_AUDIENCE", "")
    jwks_url = os.environ.get("CB_OIDC_JWKS_URL", "")
    dsn = os.environ.get("CB_DATABASE_URL", "")
    # Never permit a deployment variable to substitute a different identity
    # issuer, JWKS signing key origin, or another application's audience.
    if (issuer != "https://auth.ithute.co.ls"
            or audience != "capitalbridge"
            or jwks_url != "https://auth.ithute.co.ls/.well-known/jwks.json"
            or not dsn):
        raise RuntimeError("Trusted Ithute Auth client and finance database must be configured")
    return issuer, audience, jwks_url, dsn


def authenticate(authorization: str | None = Header(default=None)) -> UUID:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Bearer token required")
    token = authorization[7:].strip()
    if not token:
        raise HTTPException(status_code=401, detail="Bearer token required")
    issuer, audience, jwks_url, _ = config()
    try:
        key = PyJWKClient(jwks_url, cache_jwk_set=True, lifespan=300).get_signing_key_from_jwt(token).key
        claims = jwt.decode(
            token, key, algorithms=["RS256"], issuer=issuer, audience=audience,
            options={"require": ["exp", "iat", "iss", "sub", "aud"]},
            leeway=30,
        )
        subject = UUID(claims["sub"])
        if subject.int == 0:
            raise ValueError("Zero subject is not a valid Ithute user")
        return subject
    except (jwt.PyJWTError, ValueError, KeyError) as exc:
        raise HTTPException(status_code=401, detail="Invalid authentication token") from exc


def validate_company(company_id: UUID, user_id: UUID, conn: psycopg.Connection) -> None:
    # Compatibility wrapper shared with existing verified-bearer routes.
    require_company_membership(conn, company_id=company_id, user_id=user_id)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/v1/companies/{company_id}/finance/trial-balance")
def trial_balance(
    company_id: UUID,
    as_of: date = Query(...),
    user_id: UUID = Depends(authenticate),
):
    _, _, _, dsn = config()
    with psycopg.connect(dsn, row_factory=dict_row, autocommit=False) as conn:
        with conn.transaction():
            validate_company(company_id, user_id, conn)
            # The runtime DB role must not own tables or have BYPASSRLS.
            rows = conn.execute(
                """SELECT a.code, a.name,
                   COALESCE(SUM(CASE WHEN j.id IS NOT NULL
                     THEN l.debit_minor-l.credit_minor ELSE 0 END),0) AS net_minor
                   FROM cb.accounts a
                   LEFT JOIN cb.journal_lines l
                     ON l.company_id=a.company_id AND l.account_code=a.code
                   LEFT JOIN cb.journals j
                     ON j.id=l.journal_id AND j.company_id=l.company_id
                    AND j.status='posted' AND j.posted_on<=%s
                   WHERE a.company_id=%s
                   GROUP BY a.code,a.name ORDER BY a.code""",
                (as_of, company_id),
            ).fetchall()
    lines = [
        {"code": r["code"], "name": r["name"],
         "debit_minor": max(int(r["net_minor"]), 0),
         "credit_minor": max(-int(r["net_minor"]), 0)}
        for r in rows
    ]
    return {
        "company_id": str(company_id), "as_of": as_of.isoformat(),
        "currency": "LSL", "lines": lines,
        "balanced": sum(r["debit_minor"] for r in lines) == sum(r["credit_minor"] for r in lines),
    }



@app.get("/api/v1/companies/{company_id}/finance/overview")
def finance_overview(
    company_id: UUID,
    as_of: date = Query(...),
    user_id: UUID = Depends(authenticate),
):
    """Ledger-derived read model. Revenue excludes tax; bank is NOT equated to receipts."""
    _, _, _, dsn = config()
    with psycopg.connect(dsn, row_factory=dict_row, autocommit=False) as conn:
        with conn.transaction():
            validate_company(company_id, user_id, conn)
            # Treat posted journals as the authoritative source. This is a
            # preliminary finance snapshot, not a certified financial statement.
            rows = conn.execute(
                """SELECT a.kind, l.division,
                          COALESCE(SUM(CASE WHEN a.kind='revenue'
                            THEN l.credit_minor-l.debit_minor
                            ELSE l.debit_minor-l.credit_minor END),0) AS balance_minor
                   FROM cb.journal_lines l
                   JOIN cb.journals j ON j.company_id=l.company_id AND j.id=l.journal_id
                   JOIN cb.accounts a ON a.company_id=l.company_id AND a.code=l.account_code
                   WHERE l.company_id=%s AND j.status='posted' AND j.posted_on<=%s
                     AND a.kind IN ('revenue','expense')
                   GROUP BY a.kind,l.division ORDER BY l.division,a.kind""",
                (company_id, as_of),
            ).fetchall()
    revenue = sum(int(x["balance_minor"]) for x in rows if x["kind"] == "revenue")
    expenses = sum(int(x["balance_minor"]) for x in rows if x["kind"] == "expense")
    by_division = {}
    for x in rows:
        division = x["division"]
        entry = by_division.setdefault(division, {"division": division, "revenue_minor": 0, "expense_minor": 0})
        entry["revenue_minor" if x["kind"] == "revenue" else "expense_minor"] += int(x["balance_minor"])
    return {
        "company_id": str(company_id), "as_of": as_of.isoformat(), "currency": "LSL",
        "revenue_minor": revenue, "expense_minor": expenses,
        "operating_result_minor": revenue - expenses,
        "divisions": list(by_division.values()),
        "basis": "posted_journals_to_date",
    }


@app.get("/api/v1/me/companies")
def my_companies(user_id: UUID = Depends(authenticate)):
    """List only company memberships for the verified OIDC subject."""
    _, _, _, dsn = config()
    with psycopg.connect(dsn, row_factory=dict_row, autocommit=False) as conn:
        with conn.transaction():
            conn.execute("SELECT set_config('app.user_id', %s, true)", (str(user_id),))
            # RLS policy for memberships also requires company_id; enumerate
            # securely via a separate, narrowly scoped SECURITY DEFINER function.
            records = conn.execute(
                "SELECT company_id,legal_name,role FROM cb.list_my_companies()"
            ).fetchall()
    return {"companies": [
        {"id": str(r["company_id"]), "name": r["legal_name"], "role": r["role"]}
        for r in records
    ]}


@app.get("/api/v1/auth/readiness")
def authentication_readiness():
    """Public, non-sensitive rollout state. Sign-in stays disabled.

    This route intentionally does not treat environment variables, browser flags
    or a configured IdP as proof of production security readiness.
    """
    return {
        "sign_in_available": False,
        "status": "configuration_and_security_review_required",
        "message": "Secure sign-in is not yet available.",
    }


# Company-scoped CRM routes reuse the verified finance API identity boundary.
from api.clients import router as clients_router
app.include_router(clients_router)

# PDF bytes are generated exclusively by the backend after company authorisation.
from api.quotation_download import router as quotation_download_router
app.include_router(quotation_download_router)

from api.quotation_transitions import router as quotation_transitions_router
app.include_router(quotation_transitions_router)

from api.quotation_create import router as quotation_create_router
app.include_router(quotation_create_router)
