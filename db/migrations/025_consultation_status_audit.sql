BEGIN;
CREATE TABLE cb.consultation_status_audit (
 id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
 company_id uuid NOT NULL REFERENCES cb.companies(id),
 enquiry_id uuid NOT NULL,
 old_status text NOT NULL,
 new_status text NOT NULL,
 actor_id uuid NOT NULL,
 changed_at timestamptz NOT NULL DEFAULT now(),
 FOREIGN KEY(enquiry_id,company_id) REFERENCES cb.consultation_enquiries(id,company_id)
);
ALTER TABLE cb.consultation_status_audit ENABLE ROW LEVEL SECURITY;
ALTER TABLE cb.consultation_status_audit FORCE ROW LEVEL SECURITY;
CREATE POLICY consultation_audit_read ON cb.consultation_status_audit
 FOR SELECT USING(company_id=cb.authorized_company() AND cb.has_company_access(company_id));
CREATE POLICY consultation_audit_insert ON cb.consultation_status_audit
 FOR INSERT WITH CHECK(company_id=cb.authorized_company()
 AND actor_id=cb.authorized_user() AND cb.has_company_access(company_id));
REVOKE ALL ON cb.consultation_status_audit FROM PUBLIC;
CREATE INDEX consultation_audit_by_enquiry ON cb.consultation_status_audit(company_id,enquiry_id,changed_at);
COMMIT;
