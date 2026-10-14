"""Tenant provisioning policy for CapitalBridge ERP.

Pure input validation and state-transition rules. This module does not create
accounts, grant membership, alter databases or expose public API endpoints.
All database writes must be implemented behind an authorized control-plane
service with audit events and transactional idempotence.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from uuid import UUID


class TenantStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    RETIRED = "retired"


class DeploymentMode(str, Enum):
    SHARED_DATABASE = "shared_database"
    DEDICATED_DATABASE = "dedicated_database"
    DEDICATED_STACK = "dedicated_stack"
    ON_PREMISE = "on_premise"


_ALLOWED_TRANSITIONS = {
    TenantStatus.PENDING: frozenset({TenantStatus.ACTIVE, TenantStatus.RETIRED}),
    TenantStatus.ACTIVE: frozenset({TenantStatus.SUSPENDED}),
    TenantStatus.SUSPENDED: frozenset({TenantStatus.ACTIVE, TenantStatus.RETIRED}),
    TenantStatus.RETIRED: frozenset(),
}
_SLUG = re.compile(r"^[a-z][a-z0-9-]{2,62}$", re.ASCII)


@dataclass(frozen=True)
class TenantSpecification:
    company_id: UUID
    legal_name: str
    slug: str
    deployment_mode: DeploymentMode

    def __post_init__(self) -> None:
        if not isinstance(self.company_id, UUID) or self.company_id.int == 0:
            raise ValueError("Tenant company ID must be a nonzero UUID")
        if not isinstance(self.legal_name, str) or not self.legal_name.strip():
            raise ValueError("Tenant legal name is required")
        if len(self.legal_name) > 255:
            raise ValueError("Tenant legal name is too long")
        if not isinstance(self.slug, str) or not _SLUG.fullmatch(self.slug):
            raise ValueError("Tenant slug must be a valid lowercase DNS-safe slug")
        if not isinstance(self.deployment_mode, DeploymentMode):
            raise ValueError("Deployment mode is invalid")


def validate_transition(current: TenantStatus, requested: TenantStatus) -> None:
    """Fail closed for unknown lifecycle states and disallowed transitions."""
    if not isinstance(current, TenantStatus) or not isinstance(requested, TenantStatus):
        raise ValueError("Unknown tenant state")
    if requested not in _ALLOWED_TRANSITIONS[current]:
        raise ValueError(f"Tenant lifecycle transition {current.value} -> {requested.value} is not allowed")


def require_tenant_active(status: TenantStatus) -> None:
    """Policy check for future tenant-scoped operation authorization."""
    if status is not TenantStatus.ACTIVE:
        raise PermissionError("Tenant is not active")
