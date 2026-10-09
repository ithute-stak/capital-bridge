# CapitalBridge ONE + Ithute Auth

CapitalBridge is a relying party of `https://auth.ithute.co.ls`, client ID `capitalbridge`, using Authorization Code + PKCE S256, signed ID tokens from Ithute JWKS, and the existing CapitalBridge local identity mapping. Passwords, recovery, MFA and passkeys stay inside Ithute Auth. CapitalBridge users, permissions, accounting books, company memberships and sessions stay in CapitalBridge.

Server-side pinned discovery values are defined in `api/ithute_auth_provider.py`. The environment must supply `CB_ITHUTE_OIDC_REDIRECT_URI` as the **actual deployment's exact HTTPS URL** ending `/api/v1/oidc/complete`. The hostname has intentionally not been guessed. That URI must also be added verbatim to Ithute Auth's `AUTH_REDIRECT_URIS_JSON` for the `capitalbridge` client, through approved deployment configuration.

Before switching the sign-in page on: complete trusted server bootstrap and route mounting, per-request connection isolation, real Ithute Auth callback tests, code replay/MFA/session revocation/CSRF checks, production TLS, operational registration of allowed redirect URI and tested release/deployment procedures. The presence of an Ithute account never grants access without a local company membership.

This PR does **not** activate login or authorize another application to read CapitalBridge data.
