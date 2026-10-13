BEGIN;
DO $$
BEGIN
 IF NOT EXISTS (
  SELECT 1 FROM pg_roles
  WHERE rolname='cb_consultation_intake' AND NOT rolcanlogin AND NOT rolbypassrls
 ) THEN RAISE EXCEPTION 'Intake role must have NOLOGIN and NOBYPASSRLS'; END IF;
 IF NOT has_column_privilege('cb_consultation_intake','cb.consultation_enquiries','contact_name','INSERT') THEN
  RAISE EXCEPTION 'Expected narrowly scoped INSERT capability missing'; END IF;
 IF has_table_privilege('cb_consultation_intake','cb.consultation_enquiries','SELECT')
    OR has_table_privilege('cb_consultation_intake','cb.consultation_enquiries','UPDATE')
    OR has_table_privilege('cb_consultation_intake','cb.consultation_enquiries','DELETE') THEN
  RAISE EXCEPTION 'Intake has excessive enquiry permissions'; END IF;
 IF has_column_privilege('cb_consultation_intake','cb.consultation_enquiries','status','INSERT') THEN
  RAISE EXCEPTION 'Intake must not choose enquiry status'; END IF;
 IF has_table_privilege('cb_consultation_intake','cb.consultation_status_audit','INSERT') THEN
  RAISE EXCEPTION 'Intake must not forge status audit entries'; END IF;
END $$;
-- No membership rights and forced RLS: actual anonymous insertion fails closed.
SET LOCAL ROLE cb_consultation_intake;
DO $$
BEGIN
 BEGIN
  INSERT INTO cb.consultation_enquiries(
   id,company_id,contact_name,contact_email,service,message,consent_at
  ) VALUES (
   'e4000000-0000-4000-8000-000000000001',
   'e4000000-0000-4000-8000-000000000002',
   'Test Visitor','test@example.com','Information Technology',
   'This anonymous insertion must fail.',now()
  );
  RAISE EXCEPTION 'Anonymous intake INSERT unexpectedly succeeded';
 EXCEPTION WHEN insufficient_privilege OR foreign_key_violation
   OR check_violation THEN NULL;
 END;
END $$;
RESET ROLE;
ROLLBACK;
