"""Public consultation submission, guarded by explicit server rollout controls.

Must be deployed behind trusted TLS ingress and a configured Redis service.
Never use caller-selected tenant IDs or access the staff database role here.
"""
from __future__ import annotations

import json
import os
from uuid import uuid4

import psycopg
import redis
from fastapi import APIRouter, HTTPException, Request
from pydantic import ValidationError

from api.consultation_schema import ConsultationEnquiry
from api.consultation_tenant import consultation_company_id
from api.consultation_abuse_guard import validate_public_intake_headers
from api.consultation_body import read_bounded_intake_body, IntakeBodyError
from api.consultation_rate_limit import allow_intake_request, IntakeRateLimitError
from api.consultation_events import publish_consultation_change

router = APIRouter(tags=["consultation-intake"])


def intake_enabled() -> bool:
    return (os.environ.get("CB_PUBLIC_INTAKE_ENABLED") == "true" and os.environ.get("CB_PUBLIC_INTAKE_APPROVED") == "true")


def intake_dependencies():
    dsn = os.environ.get("CB_CONSULTATION_INTAKE_DSN", "")
    redis_url = os.environ.get("CB_CONSULTATION_REDIS_URL", "")
    key = os.environ.get("CB_CONSULTATION_RATE_SECRET", "")
    if not dsn or not redis_url or len(key) < 32:
        raise RuntimeError("Secure consultation intake dependencies unavailable")
    if not redis_url.startswith(("rediss://", "redis://")):
        raise RuntimeError("Invalid Redis endpoint")
    return dsn, redis_url, key


@router.post("/api/v1/consultations", status_code=201)
async def submit_public_consultation(request: Request):
    if not intake_enabled():
        raise HTTPException(status_code=503, detail="Online consultation submission is unavailable")
    # Use the peer address; only a correctly configured trusted ingress may
    # supply the true client IP. Never trust arbitrary forwarded headers.
    ip = request.client.host if request.client else ""
    try:
        declared = request.headers.get("content-length")
        size = int(declared) if declared is not None else None
        validate_public_intake_headers(
            origin=request.headers.get("origin"),
            content_type=request.headers.get("content-type"),
            content_length=size,
        )
        body = await read_bounded_intake_body(request.stream(), declared_length=size)
        payload = ConsultationEnquiry.model_validate(json.loads(body))
    except (ValueError, TypeError, json.JSONDecodeError, ValidationError, IntakeBodyError):
        raise HTTPException(status_code=400, detail="Invalid consultation request") from None
    try:
        dsn, redis_url, key = intake_dependencies()
        company = consultation_company_id()
        cache = redis.Redis.from_url(redis_url, socket_connect_timeout=2, socket_timeout=2)
        try:
            allowed = allow_intake_request(cache, trusted_client_ip=ip, secret=key)
        finally:
            cache.close()
        if not allowed:
            raise HTTPException(status_code=429, detail="Too many consultation requests")
        with psycopg.connect(dsn, autocommit=False) as db:
            with db.transaction():
                role = db.execute("""SELECT r.rolsuper,r.rolbypassrls,
                    pg_has_role(current_user,'cb_consultation_intake','USAGE') AS allowed
                    FROM pg_roles r WHERE r.rolname=current_user""").fetchone()
                if not role or role[0] or role[1] or not role[2]:
                    raise RuntimeError("Intake database role is not restricted")
                # Database policy ALSO checks company against DBA-owned configuration.
                # Do not set membership / authorization context from public requests.
                db.execute(
                    """INSERT INTO cb.consultation_enquiries
                     (id,company_id,contact_name,contact_email,contact_phone,
                      service,message,consent_at)
                     VALUES (%s,%s,%s,%s,%s,%s,%s,now())""",
                    (uuid4(),company,payload.name,str(payload.email),payload.phone,
                     payload.service.value,payload.message),
                )
    except HTTPException:
        raise
    except (RuntimeError, IntakeRateLimitError, psycopg.Error, redis.RedisError):
        raise HTTPException(status_code=503, detail="Consultation service temporarily unavailable") from None
    publish_consultation_change(company)
    return {"received": True, "message": "Your enquiry was received. Our team will review it."}
