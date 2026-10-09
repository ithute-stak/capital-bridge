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
