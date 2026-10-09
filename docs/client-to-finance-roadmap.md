# First end-to-end business workflow: client → quotation → invoice → payment → ledger

Phase 49 introduces the company-scoped client registry as the first real CRM data model and an **authenticated, read-only directory** endpoint. This is not a finished CRM: no unaudited client creation route, finance posting, quotation association or UI write workflow is activated.

Migration: `db/migrations/007_clients.sql` (unique company-specific client codes, company FK, index, RLS and director/accountant/finance-clerk write policy). Apply as migration owner.

Endpoint: `GET /api/v1/companies/{company_id}/clients?limit=50`. The existing verified Ithute bearer identity and transaction-scoped company membership check are required before querying clients; all SQL remains parameterized. The runtime PostgreSQL role must receive narrowly scoped `SELECT` permission on `cb.clients` during reviewed deployment; this migration intentionally grants none automatically. If runtime privileges are absent, access fails closed.

**Next phases:** server-authorized client creation/update with audit and input validation; quotation ownership under matching `company_id`; invoice issuance and immutable ledger posting; payment receipt and reconciliation; authenticated UI; E2E tests with PostgreSQL non-owner runtime roles; production rollback, security and data retention review.
