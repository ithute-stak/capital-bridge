-- One-time server-held OIDC login transactions. No direct browser access.
BEGIN;
CREATE TABLE cb.oidc_login_transactions (
  state_hash char(64) PRIMARY KEY,
  binding_hash char(64) NOT NULL,
  nonce text NOT NULL,
  verifier text NOT NULL,
  created_at timestamptz NOT NULL,
  expires_at timestamptz NOT NULL,
  consumed_at timestamptz,
  CHECK (expires_at > created_at),
  CHECK (consumed_at IS NULL OR consumed_at >= created_at)
);
CREATE INDEX oidc_transactions_expiry_idx ON cb.oidc_login_transactions(expires_at);
REVOKE ALL ON cb.oidc_login_transactions FROM PUBLIC;
COMMIT;
