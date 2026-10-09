# Ithute Auth trusted runtime construction

`api/ithute_runtime_factory.py` validates that all three restricted authentication database DSNs are separately configured, creates a bounded-lifetime HTTP client with redirects and inherited proxy settings disabled, verifies the fixed Ithute OIDC discovery document, then yields a LoginService. HTTP resources are closed when the context exits.

**Integration blocker:** The existing unmounted `make_ithute_oidc_router` accepts a service-returning callable, not a context-manager factory. Do not pass `ithute_login_service` directly to it. A follow-up must adapt its request lifecycle to `with ithute_login_service():` for each HTTP invocation, retain the HTTP client for the entire token-exchange operation, and run end-to-end tests. The API readiness endpoint is still disabled.

Also required before release: actual production callback allowlisting in Ithute Auth, strict PostgreSQL role credentials, secure reverse proxy/TLS, proper logout and CSRF, registered subject-to-user mapping, verified passkey/MFA flow and access revocation checks. No environment or URL values should be supplied by the browser.
