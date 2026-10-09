# CapitalBridge ONE — server-managed session design

## What is implemented
- Random, opaque session identifiers (32 random bytes, URL-safe).
- SHA-256 hashed session identifiers for server-side lookup.
- Eight-hour maximum session lifetime, checked on the server.
- Browser cookie options: `__Host-cb_session`, `Secure`, `HttpOnly`, `SameSite=Strict`, `Path=/`.
- An HTTPS same-origin check suitable as a **supplementary** CSRF guard for future state-changing routes.
- Unit tests for randomness, expiration, cookie attributes and origins.

## What is not implemented
This is a **foundation library**, not a functioning BFF session or production login. There is no OIDC callback on the server, no session database/cache, no encrypted server-side token storage, no logout endpoint, no actual cookie issuance, and no database context binding through a browser request. Do not deploy it as a complete authentication solution.

## Follow-on implementation
1. Configure a trusted OIDC provider, with issuer/JWKS and redirect allow-list.
2. Handle authorization code and PKCE on the server; validate ID token issuer, audience, signature, expiration and nonce before accepting identity.
3. Create sessions in a durable shared store and set the above cookie from the HTTPS backend only. Rotate identifier on login and privilege changes; delete it at logout.
4. Add CSRF tokens, Origin checking and strict Content Security Policy for mutation routes.
5. Resolve company authorization server-side for every request and use narrowly granted PostgreSQL role, transaction-scoped RLS context.
6. Add replay, fixation, timeouts, tenant isolation and revocation integration tests before production financial data.

The browser's OIDC PKCE prototype remains opt-in and separate from this proposed production BFF architecture.
