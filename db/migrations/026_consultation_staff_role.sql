BEGIN;
-- NOLOGIN capability role only. Operators grant this to a dedicated API role
-- after validating trusted token verification, tenant context and audit logging.
CREATE ROLE cb_consultations_staff NOLOGIN NOBYPASSRLS;
GRANT USAGE ON SCHEMA cb TO cb_consultations_staff;
GRANT SELECT ON cb.memberships TO cb_consultations_staff;
GRANT EXECUTE ON FUNCTION cb.has_company_access(uuid) TO cb_consultations_staff;
GRANT SELECT, UPDATE(status, updated_at) ON cb.consultation_enquiries TO cb_consultations_staff;
GRANT INSERT ON cb.consultation_status_audit TO cb_consultations_staff;
GRANT USAGE ON SEQUENCE cb.consultation_status_audit_id_seq TO cb_consultations_staff;
-- Do not grant public intake, company creation or audit modification.
REVOKE ALL ON cb.consultation_enquiries FROM PUBLIC;
REVOKE ALL ON cb.consultation_status_audit FROM PUBLIC;
COMMIT;
