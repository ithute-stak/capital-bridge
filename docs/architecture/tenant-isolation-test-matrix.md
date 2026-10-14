# Required tenant isolation and security test matrix

Every item is a release gate, not a claim of existing coverage.

| Test | Expected result |
|---|---|
| Tenant A user reads Tenant B ledger | Denied, no data leakage |
| Tenant A user writes Tenant B payable | Denied; no mutation |
| Forged X-Tenant-ID header | No authorization change |
| User with access to A and B switches tenant | Access scoped to selected authorized tenant only |
| Suspended tenant uses active JWT | Denied |
| Removed membership with nonexpired JWT | Denied on membership check |
| Platform operator without support grant reads bank data | Denied |
| Expired support grant | Denied and audited |
| Tenant A websocket client subscribes to B | Denied; no B events |
| Tenant A export/report/background job reads B | Denied |
| Cache keys, file objects and search index | Tenant partitioned and permission-checked |
| Bank tenant backup restored into unrelated tenant | Blocked without authorized restore procedure |
| Concurrent tenant migrations | Isolation, locking and version checks |
| SSRF/path injection on tenant routing/provisioning | Rejected |
| Integration webhooks for B delivered to A | Rejected by verified binding and signature |
| Tenant deletion, retention, legal holds | Contractual and regulatory controls enforced |
| Identity compromised / key rotation | Auditable revoke and recovery exercise |

Evidence required: automated integration tests, penetration test, disaster recovery exercise, access review, operational runbooks, and auditable change controls.
