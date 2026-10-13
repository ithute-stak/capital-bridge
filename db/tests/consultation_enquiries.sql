BEGIN;
DO $$
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
 PERFORM set_config('app.company_id','',true);
 PERFORM set_config('app.user_id','',true);
 IF EXISTS(SELECT 1 FROM cb.consultation_enquiries WHERE id=e) THEN
  RAISE EXCEPTION 'enquiry visible without company context';
 END IF;
END $$;
ROLLBACK;
