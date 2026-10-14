BEGIN;
INSERT INTO cb.companies(id,legal_name)
 VALUES ('ee000000-0000-4000-8000-000000000001','Intake Allowed'),
        ('ee000000-0000-4000-8000-000000000002','Intake Forbidden');
INSERT INTO cb.consultation_intake_config(singleton,company_id)
 VALUES(true,'ee000000-0000-4000-8000-000000000001');
SET LOCAL ROLE cb_consultation_intake;
DO $$
BEGIN
 BEGIN
  INSERT INTO cb.consultation_enquiries(id,company_id,contact_name,contact_email,
   service,message,consent_at)
  VALUES('ee000000-0000-4000-8000-000000000011',
    'ee000000-0000-4000-8000-000000000002','Other Tenant',
    'a@example.com','Information Technology','This must not be accepted.',now());
  RAISE EXCEPTION 'Cross-tenant intake write succeeded';
 EXCEPTION WHEN insufficient_privilege OR check_violation THEN NULL;
 END;
 INSERT INTO cb.consultation_enquiries(id,company_id,contact_name,contact_email,
  service,message,consent_at)
 VALUES('ee000000-0000-4000-8000-000000000012',
  'ee000000-0000-4000-8000-000000000001','Approved Tenant',
  'b@example.com','Information Technology','This is an approved enquiry.',now());
 BEGIN
  UPDATE cb.consultation_intake_config SET company_id='ee000000-0000-4000-8000-000000000002';
  RAISE EXCEPTION 'Runtime updated trusted config';
 EXCEPTION WHEN insufficient_privilege THEN NULL;
 END;
END $$;
RESET ROLE;
ROLLBACK;
