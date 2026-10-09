-- Execute after all schema migrations; fixtures are isolated and rolled back.
BEGIN;
INSERT INTO cb.companies(id,legal_name) VALUES ('a1111111-1111-4111-8111-111111111111','Invoice posting test');
INSERT INTO cb.memberships(company_id,user_id,role) VALUES ('a1111111-1111-4111-8111-111111111111','a2222222-2222-4222-8222-222222222222','accountant');
INSERT INTO cb.periods(id,company_id,starts_on,ends_on) VALUES ('a3333333-3333-4333-8333-333333333333','a1111111-1111-4111-8111-111111111111','2026-01-01','2026-12-31');
INSERT INTO cb.accounts(company_id,code,name,kind) VALUES
 ('a1111111-1111-4111-8111-111111111111','AR','Accounts receivable','asset'),
 ('a1111111-1111-4111-8111-111111111111','REV','Revenue','revenue');
INSERT INTO cb.clients(id,company_id,client_code,legal_name) VALUES ('a4444444-4444-4444-8444-444444444444','a1111111-1111-4111-8111-111111111111','TEST','Test Client');
INSERT INTO cb.invoices(id,company_id,client_id,invoice_number,issued_on,due_on,status,subtotal_minor,tax_minor)
VALUES ('a5555555-5555-4555-8555-555555555555','a1111111-1111-4111-8111-111111111111','a4444444-4444-4444-8444-444444444444','ROLLBACK-TEST','2026-10-09','2026-10-31','draft',15000,0);
INSERT INTO cb.invoice_lines(company_id,invoice_id,description,quantity,unit_price_minor)
VALUES ('a1111111-1111-4111-8111-111111111111','a5555555-5555-4555-8555-555555555555','Services',1,15000);

-- Simulate an atomic issuance containing an unbalanced journal. It must not
-- commit invoice status or a partial journal, including when a driver catches
-- the database error at an outer request boundary.
DO $$
BEGIN
 BEGIN
  INSERT INTO cb.journals(id,company_id,period_id,posted_on,reference,description,status)
  VALUES ('a6666666-6666-4666-8666-666666666666','a1111111-1111-4111-8111-111111111111',
  'a3333333-3333-4333-8333-333333333333','2026-10-09','INVOICE-ROLLBACK','Unbalanced test','draft');
  INSERT INTO cb.journal_lines(company_id,journal_id,account_code,division,debit_minor,credit_minor)
  VALUES ('a1111111-1111-4111-8111-111111111111','a6666666-6666-4666-8666-666666666666','AR','consultancy',15000,0);
  UPDATE cb.invoices SET status='issued' WHERE id='a5555555-5555-4555-8555-555555555555';
  UPDATE cb.journals SET status='posted' WHERE id='a6666666-6666-4666-8666-666666666666';
  RAISE EXCEPTION 'Unbalanced journal unexpectedly posted';
 EXCEPTION WHEN raise_exception THEN
  IF SQLERRM='Unbalanced journal unexpectedly posted' THEN RAISE; END IF;
 END;
 IF (SELECT status FROM cb.invoices WHERE id='a5555555-5555-4555-8555-555555555555') <> 'draft' THEN
   RAISE EXCEPTION 'Invoice issuance was not rolled back'; END IF;
 IF EXISTS (SELECT 1 FROM cb.journals WHERE id='a6666666-6666-4666-8666-666666666666') THEN
   RAISE EXCEPTION 'Partial journal was not rolled back'; END IF;
END $$;
ROLLBACK;
