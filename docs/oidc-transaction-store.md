# One-time OIDC login transactions

A pending login is recorded in PostgreSQL with a SHA-256 hash of its random state, a SHA-256 hash of an independent browser-binding value, the PKCE verifier, a nonce, and a five-minute expiry. `consume()` updates the pending row only when both binding and state match, it has not already been consumed, and it is unexpired. PostgreSQL's conditional UPDATE provides an atomic first-consumer-wins check. The caller **must commit the consumption before exchanging the authorization code** or invoking an external identity provider, so failed code exchange cannot roll back the consumption and permit reuse.

The browser binding must be carried only in a short-lived, Secure, HttpOnly `__Host-cb_oidc` cookie. A future server callback must verify both this cookie and the `state` response, consume and commit the transaction, exchange the code and verify the signed identity token, map the verified issuer+subject to a registered user, and only then create an authenticated session.

No callback endpoint is wired, and the login endpoint remains disabled. Production still requires restricted session database grants, encrypted-at-rest PKCE values, origin/CSP safeguards, full callback tests, deployment-integrated identity provider and durable store cleanup.
