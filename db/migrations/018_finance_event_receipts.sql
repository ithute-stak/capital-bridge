BEGIN;
CREATE TABLE cb.finance_event_receipts (
 event_id uuid PRIMARY KEY,
 company_id uuid NOT NULL REFERENCES cb.companies(id),
 received_at timestamptz NOT NULL DEFAULT now(),
 UNIQUE(company_id,event_id)
);
CREATE INDEX finance_event_receipts_company_date ON cb.finance_event_receipts(company_id,received_at DESC);
ALTER TABLE cb.finance_event_receipts ENABLE ROW LEVEL SECURITY;
ALTER TABLE cb.finance_event_receipts FORCE ROW LEVEL SECURITY;
CREATE POLICY finance_event_receipts_tenant ON cb.finance_event_receipts
 USING(company_id=cb.authorized_company() AND cb.has_company_access(company_id))
 WITH CHECK(company_id=cb.authorized_company() AND cb.has_company_access(company_id));
COMMIT;
