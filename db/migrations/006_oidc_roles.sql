-- Provision narrowly privileged authentication DB roles, with NOLOGIN until
-- an operator explicitly configures independent credentials using a secret manager.
BEGIN;
CREATE ROLE cb_oidc_transactions NOLOGIN NOBYPASSRLS;
CREATE ROLE cb_oidc_identities NOLOGIN NOBYPASSRLS;
CREATE ROLE cb_oidc_sessions NOLOGIN NOBYPASSRLS;
GRANT USAGE ON SCHEMA cb TO cb_oidc_transactions, cb_oidc_identities, cb_oidc_sessions;
GRANT SELECT, INSERT, UPDATE, DELETE ON cb.oidc_login_transactions TO cb_oidc_transactions;
GRANT SELECT ON cb.external_identities TO cb_oidc_identities;
GRANT SELECT, INSERT, UPDATE, DELETE ON cb.user_sessions TO cb_oidc_sessions;
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
COMMIT;
