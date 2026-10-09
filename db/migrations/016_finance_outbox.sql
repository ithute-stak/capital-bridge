-- Finance event outbox. Producers must insert events in the SAME transaction as their business write.
BEGIN;
CREATE TABLE cb.finance_outbox (
 id uuid PRIMARY KEY,
 company_id uuid NOT NULL REFERENCES cb.companies(id),
 event_type text NOT NULL CHECK(event_type IN ('invoice.issued','payment.posted','payment.allocated','bank.matched')),
 aggregate_id uuid NOT NULL,
 schema_version integer NOT NULL DEFAULT 1 CHECK(schema_version=1),
 payload jsonb NOT NULL DEFAULT '{}'::jsonb CHECK(jsonb_typeof(payload)='object'),
 created_at timestamptz NOT NULL DEFAULT now(),
 delivered_at timestamptz,
 attempts integer NOT NULL DEFAULT 0 CHECK(attempts>=0),
 UNIQUE(company_id,id)
);
CREATE INDEX finance_outbox_pending ON cb.finance_outbox(created_at,id) WHERE delivered_at IS NULL;
ALTER TABLE cb.finance_outbox ENABLE ROW LEVEL SECURITY;
ALTER TABLE cb.finance_outbox FORCE ROW LEVEL SECURITY;
CREATE POLICY finance_outbox_company ON cb.finance_outbox
 USING(company_id=cb.authorized_company() AND cb.has_company_access(company_id))
 WITH CHECK(company_id=cb.authorized_company() AND cb.has_company_access(company_id));
COMMIT;
