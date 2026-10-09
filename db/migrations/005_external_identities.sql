-- Link externally verified OIDC issuer+subject to existing internal users.
BEGIN;
CREATE TABLE cb.external_identities (
 issuer text NOT NULL,
 subject text NOT NULL,
 user_id uuid NOT NULL,
 created_at timestamptz NOT NULL DEFAULT now(),
 PRIMARY KEY (issuer,subject),
 CONSTRAINT external_identity_issuer_https CHECK (issuer LIKE 'https://%'),
 CONSTRAINT external_identity_subject_present CHECK (length(subject) BETWEEN 1 AND 255)
);
CREATE INDEX external_identities_user_idx ON cb.external_identities(user_id);
REVOKE ALL ON cb.external_identities FROM PUBLIC;
-- Administrative provisioning only; no self-service insert or upsert through login.
COMMIT;
