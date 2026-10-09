-- Verifies CRM record changes and notifications commit or roll back together.
-- Fixtures and the successful test transaction are rolled back on completion.
BEGIN;
INSERT INTO cb.companies(id,legal_name)
VALUES ('b1111111-1111-4111-8111-111111111111','CRM outbox integration test');
INSERT INTO cb.memberships(company_id,user_id,role)
VALUES ('b1111111-1111-4111-8111-111111111111','b2222222-2222-4222-8222-222222222222','director');
SAVEPOINT failed_crm_transaction;
INSERT INTO cb.clients(id,company_id,client_code,legal_name)
VALUES ('b3333333-3333-4333-8333-333333333333',
        'b1111111-1111-4111-8111-111111111111','ROLLBACK','Rolled back client');
INSERT INTO cb.finance_outbox(id,company_id,event_type,aggregate_id)
VALUES ('b4444444-4444-4444-8444-444444444444',
        'b1111111-1111-4111-8111-111111111111','client.created',
        'b3333333-3333-4333-8333-333333333333');
ROLLBACK TO SAVEPOINT failed_crm_transaction;
DO $$
BEGIN
 IF EXISTS (SELECT 1 FROM cb.clients WHERE id='b3333333-3333-4333-8333-333333333333')
 OR EXISTS (SELECT 1 FROM cb.finance_outbox WHERE id='b4444444-4444-4444-8444-444444444444')
 THEN RAISE EXCEPTION 'CRM rollback left a client or outbox event'; END IF;
END $$;
INSERT INTO cb.clients(id,company_id,client_code,legal_name)
VALUES ('b3333333-3333-4333-8333-333333333333',
        'b1111111-1111-4111-8111-111111111111','CREATED','Committed test client');
INSERT INTO cb.finance_outbox(id,company_id,event_type,aggregate_id)
VALUES ('b4444444-4444-4444-8444-444444444444',
        'b1111111-1111-4111-8111-111111111111','client.created',
        'b3333333-3333-4333-8333-333333333333');
DO $$
BEGIN
 IF NOT EXISTS (
  SELECT 1 FROM cb.clients c JOIN cb.finance_outbox o
  ON o.company_id=c.company_id AND o.aggregate_id=c.id
  WHERE c.id='b3333333-3333-4333-8333-333333333333'
    AND o.id='b4444444-4444-4444-8444-444444444444'
    AND o.event_type='client.created'
 ) THEN RAISE EXCEPTION 'CRM event missing or wrong company'; END IF;
END $$;
ROLLBACK;
