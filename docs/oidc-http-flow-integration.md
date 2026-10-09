# HTTP OIDC flow staging

The new `api/oidc_http_flow.py` composes login initiation, browser-bound callback validation, atomic transaction consumption, signed ID-token verification, exact registered-user mapping and server-issued secure cookie.

**It is NOT activated:** the router is not included in `api/main.py` and runtime injection is unset by default, yielding HTTP 503. The injected runtime is a test seam; it is not a production-safe database connection manager. The current login route still returns 503.

Before operational activation, replace the testing seam with a proper lifespan-scoped connection pool (separate least-privilege roles for OIDC transaction/user lookup/session writes), bind IdP config from verified server settings, atomically commit consumed transactions before making remote HTTP calls, enforce concurrent login limits, protect PKCE verifier values at rest, constrain IdP egress, add rate limits and meaningful login audit events, handle IdP errors, implement session lookup authentication in all finance routes, CSRF protection and signed-out cache clearing. Confirm full browser, provider, and database integration in CI. Do not serve production financial information through this staging component.
