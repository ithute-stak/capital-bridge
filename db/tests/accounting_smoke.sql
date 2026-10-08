-- Run as migration owner in an isolated test database.
BEGIN;
INSERT INTO cb.companies(id,legal_name) VALUES
 ('11111111-1111-4111-8111-111111111111','CapitalBridge test');
INSERT INTO cb.periods(id,company_id,starts_on,ends_on)
 VALUES ('22222222-2222-4222-8222-222222222222',
 '11111111-1111-4111-8111-111111111111','2026-01-01','2026-12-31');
INSERT INTO cb.accounts(company_id,code,name,kind) VALUES
 ('11111111-1111-4111-8111-111111111111','1000','Bank','asset'),
 ('11111111-1111-4111-8111-111111111111','4000','Revenue','revenue');
INSERT INTO cb.journals(id,company_id,period_id,posted_on,reference,description)
 VALUES ('33333333-3333-4333-8333-333333333333',
 '11111111-1111-4111-8111-111111111111',
 '22222222-2222-4222-8222-222222222222','2026-10-08','T-001','Test service payment');
INSERT INTO cb.journal_lines(company_id,journal_id,account_code,division,debit_minor,credit_minor)
 VALUES ('11111111-1111-4111-8111-111111111111','33333333-3333-4333-8333-333333333333',
 '1000','consultancy',12500,0),
 ('11111111-1111-4111-8111-111111111111','33333333-3333-4333-8333-333333333333',
 '4000','consultancy',0,12500);
UPDATE cb.journals SET status='posted' WHERE id='33333333-3333-4333-8333-333333333333';
DO $$
BEGIN
 IF (SELECT status FROM cb.journals WHERE id='33333333-3333-4333-8333-333333333333') <> 'posted'
 THEN RAISE EXCEPTION 'post failed'; END IF;
 BEGIN
  DELETE FROM cb.journal_lines WHERE journal_id='33333333-3333-4333-8333-333333333333';
  RAISE EXCEPTION 'expected immutable line rejection';
 EXCEPTION WHEN raise_exception THEN
  IF SQLERRM='expected immutable line rejection' THEN RAISE; END IF;
 END;
 BEGIN
  UPDATE cb.journals SET description='tamper' WHERE id='33333333-3333-4333-8333-333333333333';
  RAISE EXCEPTION 'expected immutable journal rejection';
 EXCEPTION WHEN raise_exception THEN
  IF SQLERRM='expected immutable journal rejection' THEN RAISE; END IF;
 END;
END $$;
ROLLBACK;
