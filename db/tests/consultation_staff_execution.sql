-- Execute inside disposable PostgreSQL CI as the migration owner.
-- Check actual row visibility and prohibited writes under a non-bypass staff role.
BEGIN;
INSERT INTO cb.companies(id,legal_name) VALUES
 ('e1000000-0000-4000-8000-000000000001','Consultation Tenant A'),
 ('e1000000-0000-4000-8000-000000000002','Consultation Tenant B');
INSERT INTO cb.memberships(company_id,user_id,role) VALUES
 ('e1000000-0000-4000-8000-000000000001','e2000000-0000-4000-8000-000000000001','director'),
 ('e1000000-0000-4000-8000-000000000002','e2000000-0000-4000-8000-000000000002','director');
INSERT INTO cb.consultation_enquiries
 (id,company_id,contact_name,contact_email,service,message,consent_at) VALUES
 ('e3000000-0000-4000-8000-000000000001','e1000000-0000-4000-8000-000000000001',
  'Tenant A Customer','a@example.com','Information Technology','A private enquiry for tenant A.',now()),
 ('e3000000-0000-4000-8000-000000000002','e1000000-0000-4000-8000-000000000002',
  'Tenant B Customer','b@example.com','Information Technology','A private enquiry for tenant B.',now());
SET LOCAL ROLE cb_consultations_staff;
SELECT set_config('app.company_id','e1000000-0000-4000-8000-000000000001',true);
SELECT set_config('app.user_id','e2000000-0000-4000-8000-000000000001',true);
DO $$
BEGIN
 IF (SELECT count(*) FROM cb.consultation_enquiries) <> 1 THEN
  RAISE EXCEPTION 'Tenant A must see precisely one consultation';
 END IF;
 IF EXISTS (SELECT 1 FROM cb.consultation_enquiries WHERE contact_email='b@example.com') THEN
  RAISE EXCEPTION 'Tenant B consultation exposed to A';
 END IF;
END $$;
-- Only changing the company claim must not grant membership in B.
SELECT set_config('app.company_id','e1000000-0000-4000-8000-000000000002',true);
DO $$
BEGIN
 IF EXISTS (SELECT 1 FROM cb.consultation_enquiries) THEN
  RAISE EXCEPTION 'Forged company context revealed another tenant';
 END IF;
END $$;
-- No identity or company context must fail closed.
SELECT set_config('app.company_id','',true);
SELECT set_config('app.user_id','',true);
DO $$
BEGIN
 IF EXISTS (SELECT 1 FROM cb.consultation_enquiries) THEN
  RAISE EXCEPTION 'Unset identity exposed consultations';
 END IF;
END $$;
SELECT set_config('app.company_id','e1000000-0000-4000-8000-000000000001',true);
SELECT set_config('app.user_id','e2000000-0000-4000-8000-000000000001',true);
DO $$
BEGIN
 BEGIN
  INSERT INTO cb.consultation_enquiries
   (id,company_id,contact_name,contact_email,service,message,consent_at)
  VALUES ('e3000000-0000-4000-8000-000000000003',
   'e1000000-0000-4000-8000-000000000001','Unauthorized','x@example.com',
   'Information Technology','Should not be insertable.',now());
  RAISE EXCEPTION 'Expected INSERT denial for staff role';
 EXCEPTION WHEN insufficient_privilege THEN NULL;
 END;
 BEGIN
  UPDATE cb.consultation_enquiries SET message='tampered'
   WHERE id='e3000000-0000-4000-8000-000000000001';
  RAISE EXCEPTION 'Expected original message UPDATE denial';
 EXCEPTION WHEN insufficient_privilege THEN NULL;
 END;
 BEGIN
  DELETE FROM cb.consultation_enquiries
   WHERE id='e3000000-0000-4000-8000-000000000001';
  RAISE EXCEPTION 'Expected enquiry DELETE denial';
 EXCEPTION WHEN insufficient_privilege THEN NULL;
 END;
 BEGIN
  UPDATE cb.consultation_status_audit SET new_status='closed' WHERE false;
  RAISE EXCEPTION 'Expected audit UPDATE denial';
 EXCEPTION WHEN insufficient_privilege THEN NULL;
 END;
END $$;
RESET ROLE;
ROLLBACK;
