# CapitalBridge ONE authentication architecture

## Stage 1 — public client OIDC/PKCE foundation

`web/oidc-session.js` is an opt-in OIDC Authorization Code + PKCE client. With no trusted `window.capitalBridgeOidcConfig`, it does nothing. The deploying operator must supply trusted issuer, endpoints, client ID and HTTPS redirect URI. The API independently validates RS256 access JWTs against pinned issuer/audience/JWKS.

- Cryptographically random state, nonce and PKCE verifier/challenge
- Reject callback with missing/mismatched/expired state
- OAuth transaction metadata in session storage; access token in memory only
- Explicit expiration handling, logout clearing local session, no automatic persistence
- HTTPS identity-provider endpoints and same-origin callback
- No client secret embedded in JavaScript

## Important production requirements

This implementation is **not a full production-grade sign-in**: it needs OIDC discovery/issuer binding, ID-token verification (including nonce), consent and auth-response error handling, token refresh/session idle limits, user-visible login/logout UI, Content Security Policy, CSRF/session architecture, proper access control tests, logout at identity provider, device controls, and secure hosting.

For high-assurance finance operations, a server-side BFF session using HttpOnly, Secure, SameSite cookies is preferred to long-lived browser bearer tokens. The current adapter provides a transitional foundation, not production approval.

Never accept unverified tokens or use a browser-provided company ID as authorization. Do not use production data until end-to-end security tests, database grants and runtime hardening pass.
