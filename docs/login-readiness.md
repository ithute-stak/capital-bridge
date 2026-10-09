# Phase 30: authentication rollout readiness

The sign-in page now reads a server-owned, same-origin readiness endpoint instead of browser-global configuration. The endpoint explicitly declares sign-in unavailable and reveals no credentials. The sign-in button remains disabled regardless of returned status, so no browser override can enable unsafe authentication.

Before changing the server to advertise live sign-in, complete and audit a genuinely mounted BFF authentication flow, IdP configuration, request-scoped restricted database roles, session-cookie issuance, logout/CSRF checks, exact issuer-subject mapping, security event logs, rate limiting, replay and cross-tenant testing, and secure deployment infrastructure. The existing demo remains distinct from financial production records.

This change is **not** live authentication and does not deploy anything.
