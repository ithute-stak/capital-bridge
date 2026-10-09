# OIDC ID token verification

`api/oidc_verify.py` validates a login ID token using a pinned HTTPS issuer/JWKS endpoint and a configured client ID. It validates the RS256 signature, issuer, audience, expiry, required time/identity claims, transaction nonce and `azp` for multi-audience ID tokens.

This module is **not wired to a login callback** and does not create a session. Before enabling sign-in, implement one-time server-side authorization transaction storage, server-to-server code exchange, ID token validation against pinned trusted metadata, robust issuer+subject to internal user mapping, and issuance of a durable, HttpOnly session only after all checks pass. Add integration tests using a real OIDC test provider and restricted database roles. The existing login route must remain disabled until then.
