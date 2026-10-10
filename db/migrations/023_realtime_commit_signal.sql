-- Transactional wake-up signal for committed notification journal inserts.
-- A PostgreSQL NOTIFY is delivered to listeners only after transaction commit;
-- rollback produces no signal. Consumers must reload by company_id and id
-- with their own authorized tenant context, never treat the signal as data access.
BEGIN;
CREATE OR REPLACE FUNCTION cb.signal_realtime_notification()
RETURNS trigger
LANGUAGE plpgsql
SECURITY INVOKER
SET search_path = pg_catalog, cb
AS $$
BEGIN
 PERFORM pg_catalog.pg_notify(
  'cb_realtime_events',
  pg_catalog.json_build_object('company_id', NEW.company_id, 'event_id', NEW.id)::text
 );
 RETURN NEW;
END;
$$;
CREATE TRIGGER realtime_notification_commit_signal
AFTER INSERT ON cb.realtime_notifications
FOR EACH ROW EXECUTE FUNCTION cb.signal_realtime_notification();
COMMIT;
