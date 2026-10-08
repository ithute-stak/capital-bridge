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

app = FastAPI(title="CapitalBridge ONE Finance API", version="0.1.0")


def config() -> tuple[str, str, str, str]:
    issuer = os.environ.get("CB_OIDC_ISSUER", "").rstrip("/")
    audience = os.environ.get("CB_OIDC_AUDIENCE", "")
    jwks_url = os.environ.get("CB_OIDC_JWKS_URL", "")
    dsn = os.environ.get("CB_DATABASE_URL", "")
    if not issuer.startswith("https://") or not jwks_url.startswith("https://") or not all((audience, dsn)):
        raise RuntimeError("OIDC issuer, audience, HTTPS JWKS URL and database URL must be configured")
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
        return UUID(claims["sub"])
    except (jwt.PyJWTError, ValueError, KeyError) as exc:
        raise HTTPException(status_code=401, detail="Invalid authentication token") from exc


def validate_company(company_id: UUID, user_id: UUID, conn: psycopg.Connection) -> None:
    # Parameterised set_config with is_local=true; a transaction is mandatory.
    conn.execute("SELECT set_config('app.company_id', %s, true)", (str(company_id),))
    conn.execute("SELECT set_config('app.user_id', %s, true)", (str(user_id),))
    row = conn.execute(
        "SELECT 1 FROM cb.memberships WHERE company_id=%s AND user_id=%s",
        (company_id, user_id),
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=403, detail="Company access denied")


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
