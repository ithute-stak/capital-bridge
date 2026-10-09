-- Durable, opaque server-side sessions. Migration owner only.
BEGIN;
CREATE TABLE cb.user_sessions (
  key_hash char(64) PRIMARY KEY,
  subject uuid NOT NULL,
  created_at timestamptz NOT NULL,
  expires_at timestamptz NOT NULL,
  revoked_at timestamptz,
  CHECK (expires_at > created_at),
  CHECK (revoked_at IS NULL OR revoked_at >= created_at)
);
CREATE INDEX user_sessions_expiry_idx ON cb.user_sessions(expires_at);
-- A service role, not end-users, needs narrow access to this table.
REVOKE ALL ON cb.user_sessions FROM PUBLIC;
COMMIT;
