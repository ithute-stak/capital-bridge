-- Structural regression: the signal is bound to notification INSERTs, not
-- HTTP acknowledgements or transaction attempts. PostgreSQL delivers NOTIFY
-- at commit and suppresses it on rollback.
DO $$
BEGIN
 IF NOT EXISTS (
  SELECT 1 FROM pg_trigger t
  JOIN pg_class c ON c.oid=t.tgrelid
  JOIN pg_namespace n ON n.oid=c.relnamespace
  WHERE n.nspname='cb' AND c.relname='realtime_notifications'
    AND t.tgname='realtime_notification_commit_signal'
    AND NOT t.tgisinternal AND t.tgenabled='O'
    AND (t.tgtype & 4)=4 AND (t.tgtype & 2)=0
 ) THEN
  RAISE EXCEPTION 'realtime notification INSERT trigger is missing or disabled';
 END IF;
END
$$;
