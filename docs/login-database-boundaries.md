# Authentication database connections

The login backend must use three **separately privileged** PostgreSQL connection roles for transaction consumption, verified identity lookup, and session issuance. `api/login_db.py` provides a fail-closed configuration reader and short-lived transactional connection context manager with rollback on exceptions, statement and lock timeouts, and optional read-only mode. It is not wired into the HTTP login flow yet.

**Security requirements before enabling login:** explicitly provision and audit restricted database roles (not owner/superuser/BYPASSRLS); separately grant only necessary table privileges; avoid connection reuse across requests; use TLS-verified connections and a secrets manager; log security events without secrets; test concurrent callback replay with real PostgreSQL, including commit-before-remote-exchange behavior; safely integrate identity and session stores; implement request-level CSRF protections and trusted provider configuration.

Different DSN strings alone are not proof of distinct database roles. Actual privileges and DB role identity must be checked in integration tests.
