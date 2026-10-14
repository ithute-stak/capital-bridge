BEGIN;
CREATE ROLE cb_consultation_notifier NOLOGIN NOBYPASSRLS;
GRANT USAGE ON SCHEMA cb TO cb_consultation_notifier;
GRANT SELECT, UPDATE(sent_at,attempts) ON cb.consultation_notification_outbox TO cb_consultation_notifier;
GRANT SELECT ON cb.consultation_enquiries TO cb_consultation_notifier;
-- Worker is a fixed application principal, not a company member. Granting
-- SELECT alone cannot bypass FORCE RLS: this role needs an explicitly reviewed
-- SECURITY DEFINER dequeue interface prior to live operation.
COMMIT;
