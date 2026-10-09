# CapitalBridge ONE — trusted server-side sign-in

This PR adds server-side OIDC Authorization Code + PKCE transaction generation and callback state verification as testable building blocks.

It does **not** implement the complete callback endpoint or enable sign-in. In particular, do not create an authenticated session from the callback's untrusted `code` or user-supplied `sub` alone.

A subsequent deployment must persist one-time OIDC transaction state in a short-lived server store, tie it to a Secure/HttpOnly/SameSite transaction cookie, exchange the code against a configured trusted HTTPS token endpoint with PKCE, verify the signed **ID token** issuer, audience, expiration, nonce, signature and allowed algorithms using pinned provider metadata, map issuer+subject to an internal user, then issue and rotate the durable opaque session. Remove consumed transactions even on errors. Apply CSRF, error handling, rate limits and logout invalidation.

The existing `/api/v1/session/login` explicitly remains HTTP 503; nothing is deployed or enabled.
