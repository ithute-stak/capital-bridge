# CapitalBridge ERP — Multi-tenant architecture (ADR-001)

Status: **proposed foundation; not production-ready**

## Ownership
CapitalBridge Consultancy (Pty) Ltd is the platform operator and product IP holder, subject to customer contracts. Each customer (e.g. Lesotho PostBank) is a tenant and remains the controller/owner of its own business data in accordance with its contract and applicable law. Platform administrative privileges do **not** grant default access to tenant financial data.

## Deployment models
1. Shared application, isolated PostgreSQL tenant databases (default for ordinary customers).
2. Dedicated application + dedicated database + dedicated network, encryption keys, and backups for regulated financial institutions.
3. Customer-managed/on-premise deployment, subject to license and support agreement.

Never mix tenant records in one table without a reviewed row-level-security strategy. Do not use a request-supplied tenant header as authority.

## Control plane
- Tenant registry: immutable UUID, slug, legal name, lifecycle state, data region, deployment mode.
- Tenant memberships and roles: platform owner is separate from tenant administrators.
- Provisioning, subscription entitlements, migrations, health, metering, support access approvals.
- Auditable tenant creation, suspension, key rotation and provisioning operations.
- No cross-tenant reports for platform staff using raw customer financial data.

## Data plane
- Per-tenant authentication/authorization, least privilege and separation of duties.
- Tenant-specific general ledger, journal entries, payables, receivables, reconciliations, procurement, assets, projects, budgets, forecasts, and audit events.
- Every tenant connection resolves via server-validated identity + membership to an approved tenant registry entry; never via user-controlled connection strings.
- Dedicated tenant-specific migrations, backup/restore, encryption, recovery tests, audit retention and legal holds.
- Prevent cross-tenant access in websocket rooms, caches, background queues, object storage, search and exports.

## Authentication rules
1. Verify issuer, signature, audience, expiry and token type.
2. Resolve user ID from verified identity, never unverified headers.
3. Authorize membership against an active tenant in the registry.
4. Compute permitted roles/scopes server-side.
5. Resolve tenant data plane using registry mapping; reject unknown, suspended or unprovisioned tenant.
6. Scope all asynchronous events and outbox records to that tenant.
7. Support explicitly time-bounded, approved, recorded break-glass support access; deny by default.

## API guidance
- Platform-owner operations: /platform/tenants, /platform/provisioning, /platform/licenses.
- Tenant-scoped operations: /api/v1/tenants/{tenant_id}/... (or subdomain routing); tenant_id is a selection, **not** an authorization grant.
- Return 404/403 consistently for nonmember tenant access.
- Background jobs, integrations, report exports, backups and websocket events must carry server-attested tenant context.
- Avoid an unauthenticated endpoint that enumerates tenants.

## Lesotho PostBank LPB/001/2026
Support bank-dedicated/on-premise deployment, FLEXCUBE integration through a separately audited connector, technical controls and audit trail, controlled data migration, financial compliance, recovery tests and training. Procurement qualification, banking references and certifications are **not** satisfied merely by adopting multitenancy.

## Rollout gates
0. Inventory actual code and database tables, including tenancy assumptions.
1. Create additive tenant registry migration with no destructive data transforms.
2. Build verified membership middleware and dedicated connection routing.
3. Introduce tenant isolation tests before migrating any financial CRUD APIs.
4. Inventory all tables/services/caches/queues/files/events and make tenant checks mandatory.
5. Provision one internal test tenant and run negative cross-tenant tests.
6. Pilot with nonproduction data and independent security review.
7. Cut over customer tenants only after recoverability, RBAC, controls and signoff.

Do not assign existing rows to a default tenant until legal ownership and tenant mapping are verified. All migrations need backup, rollback and idempotence plans.
