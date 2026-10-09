# Phase 21: OIDC callback staging

Adds validation of HTTP callback parameters and short-lived, HTTPS-only browser binding cookie options. The browser-binding cookie uses `SameSite=Lax` rather than Strict because the OIDC provider returns the user via a top-level navigation from a different site. The authenticated session cookie stays separate and uses stricter settings.

`api/oidc_callback_routes.py` is an **unregistered** staging router that returns HTTP 503 for correctly shaped callbacks; invalid callbacks are rejected. No callback can create a session. The login endpoint is still disabled.

Production activation requires secure one-time login initiation, database transaction persistence and atomic consume, trusted server-side OIDC code exchange and signed token verification, verified internal identity mapping, encrypted storage permissions, precise redirect origin allowlisting, integration with trusted IdP, CSRF and callback replay tests, logout/session invalidation, and privileged-operation threat review. Authentication must remain disabled until these requirements are satisfied.
