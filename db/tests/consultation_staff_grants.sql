BEGIN;
DO $$
BEGIN
 IF NOT EXISTS(SELECT 1 FROM pg_roles WHERE rolname='cb_consultations_staff' AND NOT rolcanlogin AND NOT rolbypassrls) THEN
  RAISE EXCEPTION 'Staff capability role must be NOLOGIN NOBYPASSRLS';
 END IF;
 IF NOT has_table_privilege('cb_consultations_staff','cb.consultation_enquiries','SELECT') THEN
  RAISE EXCEPTION 'Staff enquiry read privilege missing';
 END IF;
 IF NOT has_column_privilege('cb_consultations_staff','cb.consultation_enquiries','status','UPDATE') THEN
  RAISE EXCEPTION 'Staff enquiry status update privilege missing';
 END IF;
 IF has_column_privilege('cb_consultations_staff','cb.consultation_enquiries','message','UPDATE') THEN
  RAISE EXCEPTION 'Staff must not edit original enquiry message';
 END IF;
 IF has_table_privilege('cb_consultations_staff','cb.consultation_enquiries','INSERT')
    OR has_table_privilege('cb_consultations_staff','cb.consultation_enquiries','DELETE') THEN
  RAISE EXCEPTION 'Staff must not insert or delete enquiries';
 END IF;
 IF NOT has_table_privilege('cb_consultations_staff','cb.consultation_status_audit','INSERT') THEN
  RAISE EXCEPTION 'Audit writer privilege missing';
 END IF;
 IF has_table_privilege('cb_consultations_staff','cb.consultation_status_audit','SELECT')
    OR has_table_privilege('cb_consultations_staff','cb.consultation_status_audit','UPDATE')
    OR has_table_privilege('cb_consultations_staff','cb.consultation_status_audit','DELETE') THEN
  RAISE EXCEPTION 'Audit write role has excessive privileges';
 END IF;
END $$;
ROLLBACK;
