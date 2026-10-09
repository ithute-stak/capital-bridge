# Phase 32: Session-backed finance identity

`api/finance_session_auth.py` provides a staging dependency that resolves an opaque, HttpOnly session cookie through the restricted session-store database role. Missing and revoked sessions are rejected with HTTP 401. The identity is always derived server-side; the browser cannot choose a user ID.

**Not activated:** the dependency is not registered on the finance API. Financial endpoints currently use bearer-token OIDC verification, and the actual BFF login remains disabled. Before activating cookie-based finance access, validate working trusted IdP login and logout, CSRF defenses for mutations, deployment TLS and cookie configuration, strict company authorization under RLS for every endpoint, session-store availability, and multi-company end-to-end tests. The dashboard still uses demonstration figures until integration is fully verified.
