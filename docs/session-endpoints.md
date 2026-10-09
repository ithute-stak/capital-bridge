# CapitalBridge ONE — session endpoint staging

The new BFF endpoints are deliberately minimal.

- `GET /api/v1/session/status`: only reports authenticated or signed out; reads the durable session store when an opaque HttpOnly cookie exists.
- `POST /api/v1/session/logout`: same-origin HTTPS request only; revokes a presented session and expires the cookie.
- `POST /api/v1/session/login`: returns HTTP 503 until verified OIDC callback and subject mapping exist.

These routes remain **opt-in** until explicitly registered in the FastAPI application. The session database account must be dedicated and narrowly privileged. Production requires correct reverse-proxy trusted-origin handling, rate limits, CSRF token checks in addition to Origin, real OIDC state/nonce verification, issuance, role checks, secured log sanitisation, session store load testing, and end-to-end regression tests.

Never treat a client-supplied user identifier as authenticated identity.
