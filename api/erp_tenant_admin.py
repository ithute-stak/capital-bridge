"""Fail-closed platform-only ERP tenant onboarding service.

Not mounted as a public HTTP route. Callers must supply a dedicated control-plane
connection authenticated as a restricted database role, never the finance role.
The database must independently authorize mutations; Python validation is not
a substitute for SQL grants, audit, or operator authentication.
"""
from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from api.erp_tenant_policy import DeploymentMode, TenantSpecification


@dataclass(frozen=True)
class ProvisioningResult:
    tenant_id: UUID
    status: str


def register_pending_tenant(connection, *, spec: TenantSpecification, operator_id: UUID) -> ProvisioningResult:
    """Register a pending tenant, and record who requested it, atomically.

    SQL cb.register_erp_tenant performs privilege validation and auditing.
    No user-provided database routing, password or role grant is accepted.
    """
    if not isinstance(spec, TenantSpecification):
        raise ValueError("Validated tenant specification required")
    if not isinstance(operator_id, UUID) or operator_id.int == 0:
        raise ValueError("Verified operator UUID required")
    record = connection.execute(
        "SELECT tenant_id, tenant_status FROM cb.register_erp_tenant(%s,%s,%s,%s,%s)",
        (operator_id, spec.company_id, spec.legal_name.strip(),
         spec.slug, spec.deployment_mode.value),
    ).fetchone()
    if record is None or record[0] != spec.company_id or record[1] != "pending":
        raise RuntimeError("Tenant registration was not confirmed")
    return ProvisioningResult(record[0], record[1])
