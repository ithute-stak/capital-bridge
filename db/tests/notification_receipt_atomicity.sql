-- Genuine PostgreSQL atomicity and deduplication regression.
BEGIN;
INSERT INTO cb.companies(id,legal_name) VALUES
 ('c1111111-1111-4111-8111-111111111111','Notification atomicity fixture');
INSERT INTO cb.memberships(company_id,user_id,role) VALUES
 ('c1111111-1111-4111-8111-111111111111','c2222222-2222-4222-8222-222222222222','director');
SELECT set_config('app.company_id','c1111111-1111-4111-8111-111111111111',true);
SAVEPOINT failed_delivery;
INSERT INTO cb.finance_event_receipts(event_id,company_id)
 VALUES('c3333333-3333-4333-8333-333333333333','c1111111-1111-4111-8111-111111111111');
-- Invalid event type makes the notification insert fail, requiring rollback.
DO $$
BEGIN
 BEGIN
  INSERT INTO cb.realtime_notifications(id,company_id,event_type,aggregate_id)
   VALUES('c3333333-3333-4333-8333-333333333333',
    'c1111111-1111-4111-8111-111111111111','invalid.type',
    'c4444444-4444-4444-8444-444444444444');
  RAISE EXCEPTION 'Invalid event notification was accepted';
 EXCEPTION WHEN check_violation THEN
  NULL;
 END;
END $$;
ROLLBACK TO SAVEPOINT failed_delivery;
DO $$
BEGIN
 IF EXISTS(SELECT 1 FROM cb.finance_event_receipts WHERE event_id='c3333333-3333-4333-8333-333333333333')
 THEN RAISE EXCEPTION 'Receipt survived failed transaction'; END IF;
END $$;
INSERT INTO cb.finance_event_receipts(event_id,company_id)
 VALUES('c3333333-3333-4333-8333-333333333333','c1111111-1111-4111-8111-111111111111');
INSERT INTO cb.realtime_notifications(id,company_id,event_type,aggregate_id)
 VALUES('c3333333-3333-4333-8333-333333333333','c1111111-1111-4111-8111-111111111111',
 'client.updated','c4444444-4444-4444-8444-444444444444');
-- Duplicate receipt must not create a duplicate event.
INSERT INTO cb.finance_event_receipts(event_id,company_id)
 VALUES('c3333333-3333-4333-8333-333333333333','c1111111-1111-4111-8111-111111111111')
 ON CONFLICT(event_id) DO NOTHING;
DO $$
BEGIN
 IF (SELECT count(*) FROM cb.finance_event_receipts WHERE event_id='c3333333-3333-4333-8333-333333333333')<>1
 OR (SELECT count(*) FROM cb.realtime_notifications WHERE id='c3333333-3333-4333-8333-333333333333')<>1
 THEN RAISE EXCEPTION 'Duplicate delivery or missing notification'; END IF;
END $$;
ROLLBACK;
