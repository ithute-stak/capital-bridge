# CapitalBridge Go notification ingress: managed service

Phase 105 supplies a systemd template only. No remote host is altered or activated.

Before deployment, an administrator must:
1. Create a dedicated non-login `capitalbridge-ingress` service account and private `/etc/capitalbridge` directory.
2. Provision `/etc/capitalbridge/go-ingress.env` outside Git with permissions restricting access to the service operator, containing the variables required by `ReadServiceConfig`: `CB_GO_LISTEN`, `CB_GO_COMPANY_ID`, `CB_GO_DATABASE_URL`, `CB_GO_TLS_CERT_FILE`, `CB_GO_TLS_KEY_FILE`, and `CB_GO_DELIVERY_HMAC_KEY`.
3. Provision a valid TLS certificate and private key readable by the service account, and a company-scoped PostgreSQL `cb_go_delivery` account using `sslmode=verify-full`; restrict inbound traffic to trusted internal callers.
4. Compile the binary using `bash services/go/build-ingress.sh` and install it at `/opt/capitalbridge/bin/capitalbridge-go-ingress` with executable permission.
5. Validate PostgreSQL schema migrations through 022, TLS trust, event sender HMAC agreement, and service role grants. Check restrictive systemd paths for certificate access.
6. Stage installation and exercise signed accepted / duplicate / invalid / revoked company events; confirm that a database outage returns non-success and outbox retries.
7. Only after tests pass, install the service unit, explicitly enable/start it with systemd, observe health, errors and alerting, and document rollback.

**Not done here:** no provisioning, secrets, production systemd actions, database connectivity testing, runtime health monitoring, or actual multi-node delivery test. A dedicated unit is scoped to ONE company UUID; deployment for multiple companies needs separately configured isolated instances or an authenticated multi-company service redesign.
