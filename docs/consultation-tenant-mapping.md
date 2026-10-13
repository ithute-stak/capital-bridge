# Trusted consultation tenant mapping

The public CapitalBridge website belongs to one approved company. Before public
POST intake is implemented, deployment operators must provision
`CB_CONSULTATION_COMPANY_ID` to that company's UUID from the authoritative
`cb.companies` registry. This value must be stored only in a protected backend
deployment environment/secret manager, not in HTML, JavaScript or a URL parameter.

`api.consultation_tenant.consultation_company_id()` validates and returns the
server-owned UUID and fails closed if missing, invalid or zero. It deliberately
does **not** read a client-supplied company ID, Origin, or Host to choose a tenant.

## Not yet implemented

No public submission endpoint has been enabled. Configuration parsing is not
proof of membership or authorization. A future intake implementation needs a
restricted write path and real PostgreSQL RLS tests, abuse controls at the edge,
privacy and retention approval, consent, monitoring and end-to-end tests before
intake readiness can be changed to true. Existing staff functionality remains
protected by Ithute Auth and company-membership checks.
