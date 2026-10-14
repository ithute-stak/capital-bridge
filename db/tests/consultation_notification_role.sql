BEGIN;
DO $$
BEGIN
 IF NOT has_column_privilege('cb_consultation_notifier','cb.consultation_enquiries','contact_name','SELECT')
  OR has_column_privilege('cb_consultation_notifier','cb.consultation_enquiries','message','SELECT') THEN
  RAISE EXCEPTION 'Notifier read grants incorrect';
 END IF;
 IF has_table_privilege('cb_consultation_notifier','cb.consultation_enquiries','UPDATE')
  OR has_table_privilege('cb_consultation_notifier','cb.consultation_enquiries','INSERT') THEN
  RAISE EXCEPTION 'Notifier may mutate customer enquiries';
 END IF;
END $$;
ROLLBACK;
