"""Unmounted, fail-closed control-plane gateway for ERP tenant operations.

Only the trusted finance OIDC verifier may produce the operator UUID.
Never accept operator_id, database credentials, role, or deployment DSN from
the request body. This router is NOT mounted in api.main and is not live.
Deployment requires isolated network credentials, operator enrollment controls,
and an independently reviewed session/SQL identity binding.
"""
from __future__ import annotations

from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from api.main import authenticate
from api.erp_tenant_admin import register_pending_tenant, transition_tenant
from api.erp_tenant_policy import DeploymentMode, TenantSpecification

router = APIRouter(prefix="/api/v1/platform/tenants", tags=["platform-control-plane"])


class RegisterTenantRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    legal_name: str = Field(min_length=1, max_length=255)
    slug: str
    deployment_mode: DeploymentMode


class TransitionTenantRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    expected_status: str
    target_status: str


def _disabled_control_plane():
    # Explicit release gate. No environment variable or browser flag enables
    # writes until the backend security boundary is reviewed and implemented.
    raise HTTPException(status_code=503, detail="ERP platform administration is not enabled")


@router.post("", status_code=201)
def register_tenant(
    payload: RegisterTenantRequest,
    operator: UUID = Depends(authenticate),
    connection=Depends(_disabled_control_plane),
):
    spec = TenantSpecification(
        uuid4(), payload.legal_name, payload.slug, payload.deployment_mode
    )
    return register_pending_tenant(connection, spec=spec, operator_id=operator)


@router.post("/{tenant_id}/transition")
def change_tenant_status(
    tenant_id: UUID,
    payload: TransitionTenantRequest,
    operator: UUID = Depends(authenticate),
    connection=Depends(_disabled_control_plane),
):
    return {"status": transition_tenant(
        connection, tenant_id=tenant_id, operator_id=operator,
        expected_status=payload.expected_status,
        target_status=payload.target_status,
    )}
