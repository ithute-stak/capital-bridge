BEGIN;
CREATE ROLE cb_consultation_test NOLOGIN NOBYPASSRLS;
GRANT USAGE ON SCHEMA cb TO cb_consultation_test;
GRANT SELECT ON cb.consultation_enquiries,cb.memberships TO cb_consultation_test;
GRANT EXECUTE ON FUNCTION cb.has_company_access(uuid) TO cb_consultation_test;
DO $
DECLARE
 c uuid := 'e0000000-0000-4000-8000-000000000001';
 u uuid := 'e0000000-0000-4000-8000-000000000002';
 e uuid := 'e0000000-0000-4000-8000-000000000003';
BEGIN
 INSERT INTO cb.companies(id,legal_name) VALUES(c,'Consultation DB Test');
 INSERT INTO cb.memberships(company_id,user_id,role) VALUES(c,u,'director');
 PERFORM set_config('app.company_id',c::text,true);
 PERFORM set_config('app.user_id',u::text,true);
 INSERT INTO cb.consultation_enquiries(id,company_id,contact_name,contact_email,service,message,consent_at)
 VALUES(e,c,'Consultation Test','test@example.com','Information Technology',
 'Please contact us regarding our project.',now());
 IF NOT EXISTS(SELECT 1 FROM cb.consultation_enquiries WHERE id=e AND status='new') THEN
  RAISE EXCEPTION 'enquiry was not stored with new status';
 END IF;
 -- Visibility checks run outside the owner DO block as an NOBYPASSRLS role.
END $;
SET LOCAL ROLE cb_consultation_test;
SELECT set_config('app.company_id','',true);
SELECT set_config('app.user_id','',true);
DO $
BEGIN
 IF EXISTS(SELECT 1 FROM cb.consultation_enquiries) THEN
  RAISE EXCEPTION 'enquiry visible without company context';
 END IF;
END $;
RESET ROLE;
ROLLBACK;
