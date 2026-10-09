BEGIN;
GRANT INSERT ON cb.realtime_notifications TO cb_go_delivery;
DROP POLICY IF EXISTS go_delivery_notification_insert ON cb.realtime_notifications;
CREATE POLICY go_delivery_notification_insert ON cb.realtime_notifications
 FOR INSERT TO cb_go_delivery WITH CHECK(company_id=cb.authorized_company());
COMMIT;
