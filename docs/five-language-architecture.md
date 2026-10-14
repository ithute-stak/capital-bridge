# CapitalBridge ONE — Five-language architecture

This milestone introduces **tested, isolated prototypes**. They are not connected to financial posting, authenticated API routes, WebSockets, or production deployment.

| Language | Responsibility | Initial prototype |
|---|---|---|
| Python | Finance API and request/workflow orchestration | Validated, versioned event envelope |
| Java | Enterprise approvals and policy rules | Deterministic dual-review recommendation |
| C++ | High-throughput exact monetary computations | Integer minor-unit payment allocation |
| Go | Event distribution and realtime transport boundary | Validates a versioned event envelope on stdin |
| Rust | Cryptographic evidence and integrity | SHA-256 digest of exact input bytes |

**Security contract:** no component independently authenticates users, grants tenant access, or commits ledger entries. Python/PostgreSQL remain authoritative for identity, company scoping and journal posting. Values representing money use signed 64-bit minor units, never floating point. Go events carry company identifiers but receivers must still authorize on the server. Hashing bytes is not a signed, tamper-proof audit log; durable chained signatures, secret management, message broker delivery, retries and observability are separate milestones.

**Next integration:** define a canonical JSON/Protobuf contract, authenticated internal transports (mTLS), PostgreSQL transactional outbox, idempotency, and end-to-end tests before activating any cross-language service.


## ERP platform language ownership (2026-10-14)

The five backend languages remain intentional. JavaScript and PostgreSQL SQL
are also first-class production components, giving **seven technologies** in
the application, not seven independent authorities over tenant or ledger data.

| Technology | Existing evidence | ERP target | Current limitation |
|---|---|---|---|
| Python | `api/main.py`, `api/finance_authorization.py`, `accounting/` | Authenticated finance APIs, transaction orchestration, tenant control plane | Tenant lifecycle validation exists but no live provisioning API or status enforcement yet |
| Go | `services/go/outbox_delivery/` incl. tenant-hub and admission tests | Durable tenant-scoped event delivery, notifications, realtime transports | Must retain user, membership, event and tenant authorization checks |
| Java | `services/java/src/ApprovalPolicy.java` | Approval and segregation-of-duties policy calculations | Standalone prototype; cannot grant user permissions |
| C++ | `services/cpp/payment_allocation.cpp` | Exact integer minor-unit computation in performance-critical batch jobs | Standalone prototype; not a ledger authority |
| Rust | `services/rust/audit/src/main.rs` | Evidence integrity and crypto-sensitive validations | Hashing alone is not immutable, signed, independently verifiable audit history |
| JavaScript | `web/` vanilla JavaScript and CSS | Responsive tenant-aware ERP screens, admin console, live updates | Never the authoritative source of tenant permission or financial totals |
| PostgreSQL SQL | `db/migrations/`, `db/tests/` | RLS, ACID posting, tenant state and company scoped consistency | Current deployment remains shared-database; dedicated tenant routing is not implemented |

### Nonnegotiable language boundaries

1. Only a trusted backend backed by PostgreSQL may authorize and commit financial transactions. Java/C++/Rust output is advisory until verified server-side.
2. Tenant identity derives from verified login and live membership, **not** the browser, a tenant ID header, Go message body or an embedded tenant ID alone.
3. All cross-language requests/events carry an immutable correlation ID and validated canonical tenant UUID. Use explicit JSON/Protobuf schemas with versioning.
4. Money is represented in integer minor units with checked arithmetic; no float conversions across service boundaries.
5. Support bank-dedicated deployments with independently scoped credentials, storage, encryption keys, audit evidence and backups.
6. CI must cover Python, Go, Java, C++, Rust, JavaScript and PostgreSQL, including tenant negative tests, contract version mismatches, unauthorized background jobs and data integrity. A build success does not imply production readiness.
7. New languages or services are introduced only for a measurable engineering need; do not move mature business logic to satisfy an arbitrary language-count requirement.

### Acceptance gates

- Cross-tenant reads/writes, WebSocket subscriptions, exports and queued messages denied.
- Suspension and membership revocation effective without accepting stale authenticated sessions.
- Multi-language monetary and event contract fixtures match exactly, including overflow/invalid input.
- Production release requires reviewed migrations, security assessment, observability, rollback procedures and verified CI.
