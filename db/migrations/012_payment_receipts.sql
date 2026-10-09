-- Receipt records are only publishable after a verified payment and posted cash journal.
BEGIN;
CREATE TABLE cb.payment_receipts (
 id uuid PRIMARY KEY,
 company_id uuid NOT NULL,
 payment_id uuid NOT NULL,
 journal_id uuid NOT NULL,
 receipt_number text NOT NULL CHECK(length(btrim(receipt_number)) BETWEEN 1 AND 80),
 amount_minor bigint NOT NULL CHECK(amount_minor>0),
 issued_at timestamptz NOT NULL DEFAULT now(),
 issued_by uuid NOT NULL,
 UNIQUE(company_id,receipt_number),
 UNIQUE(company_id,payment_id),
 FOREIGN KEY(company_id,payment_id) REFERENCES cb.client_payments(company_id,id),
 FOREIGN KEY(journal_id,company_id) REFERENCES cb.journals(id,company_id)
);
CREATE INDEX receipts_by_company_date ON cb.payment_receipts(company_id,issued_at DESC);
ALTER TABLE cb.payment_receipts ENABLE ROW LEVEL SECURITY;
ALTER TABLE cb.payment_receipts FORCE ROW LEVEL SECURITY;
CREATE POLICY receipt_company_read ON cb.payment_receipts FOR SELECT
 USING(company_id=cb.authorized_company() AND cb.has_company_access(company_id));
CREATE POLICY receipt_company_insert ON cb.payment_receipts FOR INSERT
 WITH CHECK(company_id=cb.authorized_company() AND issued_by=cb.authorized_user()
 AND cb.has_company_access(company_id));
COMMIT;
