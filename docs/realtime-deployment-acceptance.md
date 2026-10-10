# Real-time deployment acceptance checklist

This repository is not yet deployed to production. A green GitHub Actions run does not activate runtime services.

Required before enabling a user-facing live status:
- Trusted server-side Ithute OIDC callback and a verified issued session cookie
- Configured PostgreSQL accounting and restricted session database credentials
- TLS-protected Go ingress using the atomic notification writer and appropriately restricted database role
- Running Python outbox delivery worker with retries and monitoring
- Running Go HTTP service (existing handler alone is not a server)
- Migrations through 022 applied, verified notification persistence and multiple-app-instance reader access
- Server-side membership revocation testing and browser backfill/resynchronisation after disconnect
- Reconciled credentials for each deployment and documented rollback

The readiness helper evaluates configuration flags only and does not start services, ping a database or prove end-to-end delivery. Never use it alone as proof of operational readiness.
