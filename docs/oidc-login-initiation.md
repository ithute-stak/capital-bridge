# OIDC login initiation

The `initiate_login` helper creates a random PKCE login transaction, an independent browser-binding secret, saves only a SHA-256 hash of the binding in PostgreSQL, and commits the transaction before returning an authorization URL.

This module does **not** register a live login endpoint or redirect browser traffic. A trusted HTTPS route must later issue the binding as a Secure, HttpOnly, SameSite=Lax, short-lived cookie and redirect only to a statically configured identity provider after CSRF, deployment-domain, and reverse-proxy checks. The callback must atomically consume the transaction, commit consumption before token exchange, validate the signed ID token and map to a registered user before creating the actual session. Role and DB privileges need production integration testing before activation.

Login remains disabled.
