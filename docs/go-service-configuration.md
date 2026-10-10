# Go ingress service configuration (Phase 101)

This phase validates the Go ingress configuration but does **not** provision or start a production database-backed daemon.

Required environment keys: `CB_GO_LISTEN`, `CB_GO_COMPANY_ID` (one UUID-scoped company), `CB_GO_DATABASE_URL` using username `cb_go_delivery` and `sslmode=verify-full`, `CB_GO_TLS_CERT_FILE`, `CB_GO_TLS_KEY_FILE`, `CB_GO_DELIVERY_HMAC_KEY` (32 or more bytes).

Never commit actual credentials. PostgreSQL login passwords must be provisioned out of band. A full server entrypoint still needs a PostgreSQL driver, connection pool with bounded lifetime, graceful operating-system signal handling, `AtomicNotificationStore` wiring and deployment instructions. Actual TLS key pair validity and connectivity are enforced at startup by runtime implementation, not this configuration parser alone.
