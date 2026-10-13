BEGIN;
-- Isolated NOLOGIN capability for future public intake service.
-- Granting INSERT does NOT bypass the existing RLS membership policy.
-- No public HTTP handler or trusted tenant assignment is activated.
CREATE ROLE cb_consultation_intake NOLOGIN NOBYPASSRLS;
GRANT USAGE ON SCHEMA cb TO cb_consultation_intake;
GRANT INSERT (id,company_id,contact_name,contact_email,contact_phone,
 service,message,consent_at) ON cb.consultation_enquiries TO cb_consultation_intake;
REVOKE ALL ON cb.consultation_enquiries FROM PUBLIC;
-- Intentionally no SELECT, UPDATE, DELETE, membership or bypass grants.
-- Existing FORCE RLS prevents anonymous insert; a subsequent reviewed
-- deployment must add trusted server-side intake mediation and tests.
COMMIT;
