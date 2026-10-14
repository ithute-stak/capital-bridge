BEGIN;
CREATE ROLE cb_consultation_notifier NOLOGIN NOBYPASSRLS;
GRANT USAGE ON SCHEMA cb TO cb_consultation_notifier;
GRANT EXECUTE ON FUNCTION cb.approved_consultation_tenant() TO cb_consultation_notifier;
-- Other permissive RLS policies may evaluate membership as part of OR conditions.
GRANT EXECUTE ON FUNCTION cb.has_company_access(uuid) TO cb_consultation_notifier;
GRANT SELECT, UPDATE(sent_at,attempts) ON cb.consultation_notification_outbox TO cb_consultation_notifier;
GRANT SELECT(id,company_id,service,contact_name) ON cb.consultation_enquiries TO cb_consultation_notifier;
CREATE POLICY consultation_notifier_read ON cb.consultation_enquiries
 FOR SELECT TO cb_consultation_notifier
 USING(company_id=cb.approved_consultation_tenant());
CREATE POLICY consultation_outbox_notifier_read ON cb.consultation_notification_outbox
 FOR SELECT TO cb_consultation_notifier
 USING(company_id=cb.approved_consultation_tenant());
CREATE POLICY consultation_outbox_notifier_update ON cb.consultation_notification_outbox
 FOR UPDATE TO cb_consultation_notifier
 USING(company_id=cb.approved_consultation_tenant())
 WITH CHECK(company_id=cb.approved_consultation_tenant());
-- No company membership grant, no ability to edit the customer's original
-- enquiry and no ability to delete or alter the event source.
COMMIT;
