BEGIN;
ALTER TABLE cb.finance_outbox DROP CONSTRAINT finance_outbox_event_type_check;
ALTER TABLE cb.finance_outbox ADD CONSTRAINT finance_outbox_event_type_check
 CHECK(event_type IN ('invoice.issued','payment.posted','payment.allocated','bank.matched','client.created','client.updated'));
ALTER TABLE cb.realtime_notifications DROP CONSTRAINT realtime_notifications_event_type_check;
ALTER TABLE cb.realtime_notifications ADD CONSTRAINT realtime_notifications_event_type_check
 CHECK(event_type IN ('invoice.issued','payment.posted','payment.allocated','bank.matched','client.created','client.updated'));
COMMIT;
