BEGIN;
-- DB-owned company mapping. Runtime intake role cannot read or change this.
CREATE TABLE cb.consultation_intake_config (
 singleton boolean PRIMARY KEY DEFAULT true CHECK(singleton),
 company_id uuid NOT NULL REFERENCES cb.companies(id)
);
REVOKE ALL ON cb.consultation_intake_config FROM PUBLIC;
CREATE FUNCTION cb.approved_consultation_tenant() RETURNS uuid
 LANGUAGE sql STABLE SECURITY DEFINER SET search_path = cb, pg_temp AS $$
 SELECT company_id FROM cb.consultation_intake_config WHERE singleton IS TRUE
$$;
REVOKE ALL ON FUNCTION cb.approved_consultation_tenant() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION cb.approved_consultation_tenant() TO cb_consultation_intake;
-- DB checks tenant independently; the API cannot choose another tenant via a
-- submitted company id or session custom setting. Only INSERT is permitted.
CREATE POLICY consultation_intake_approved_insert ON cb.consultation_enquiries
 FOR INSERT TO cb_consultation_intake
 WITH CHECK(company_id = cb.approved_consultation_tenant()
 AND status='new' AND consent_at IS NOT NULL);
COMMIT;
