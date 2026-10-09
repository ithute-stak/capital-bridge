-- Backend payment, receipt and allocation foundation. No posting API activated.
BEGIN;
CREATE TABLE cb.client_payments (
 id uuid PRIMARY KEY,
 company_id uuid NOT NULL REFERENCES cb.companies(id),
 client_id uuid NOT NULL,
 payment_reference text NOT NULL CHECK (length(btrim(payment_reference)) BETWEEN 1 AND 80),
 paid_on date NOT NULL,
 method text NOT NULL CHECK(method IN ('bank_transfer','cash','card','mobile_money','other')),
 amount_minor bigint NOT NULL CHECK(amount_minor > 0),
 currency char(3) NOT NULL DEFAULT 'LSL' CHECK(currency='LSL'),
 status text NOT NULL DEFAULT 'pending' CHECK(status IN ('pending','verified','reversed')),
 created_at timestamptz NOT NULL DEFAULT now(),
 UNIQUE(company_id,payment_reference),
 UNIQUE(company_id,id),
 FOREIGN KEY(company_id,client_id) REFERENCES cb.clients(company_id,id)
);
CREATE TABLE cb.payment_allocations (
 id uuid PRIMARY KEY,
 company_id uuid NOT NULL,
 payment_id uuid NOT NULL,
 invoice_id uuid NOT NULL,
 amount_minor bigint NOT NULL CHECK(amount_minor>0),
 allocated_at timestamptz NOT NULL DEFAULT now(),
 UNIQUE(company_id,payment_id,invoice_id),
 FOREIGN KEY(company_id,payment_id) REFERENCES cb.client_payments(company_id,id),
 FOREIGN KEY(company_id,invoice_id) REFERENCES cb.invoices(company_id,id)
);
CREATE INDEX payments_company_client ON cb.client_payments(company_id,client_id,paid_on DESC);
CREATE INDEX allocations_invoice ON cb.payment_allocations(company_id,invoice_id);
CREATE TABLE cb.payment_reconciliation_events (
 id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
 company_id uuid NOT NULL,
 payment_id uuid NOT NULL,
 actor_user_id uuid NOT NULL,
 result text NOT NULL CHECK(result IN ('matched','partial','disputed')),
 evidence_reference text NOT NULL CHECK(length(btrim(evidence_reference))>0),
 reconciled_at timestamptz NOT NULL DEFAULT now(),
 FOREIGN KEY(company_id,payment_id) REFERENCES cb.client_payments(company_id,id)
);
ALTER TABLE cb.client_payments ENABLE ROW LEVEL SECURITY;
ALTER TABLE cb.client_payments FORCE ROW LEVEL SECURITY;
ALTER TABLE cb.payment_allocations ENABLE ROW LEVEL SECURITY;
ALTER TABLE cb.payment_allocations FORCE ROW LEVEL SECURITY;
ALTER TABLE cb.payment_reconciliation_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE cb.payment_reconciliation_events FORCE ROW LEVEL SECURITY;
CREATE POLICY payment_tenant ON cb.client_payments
 USING(company_id=cb.authorized_company() AND cb.has_company_access(company_id))
 WITH CHECK(company_id=cb.authorized_company() AND cb.has_company_access(company_id));
CREATE POLICY allocation_tenant ON cb.payment_allocations
 USING(company_id=cb.authorized_company() AND cb.has_company_access(company_id))
 WITH CHECK(company_id=cb.authorized_company() AND cb.has_company_access(company_id));
CREATE POLICY reconciliation_tenant ON cb.payment_reconciliation_events
 USING(company_id=cb.authorized_company() AND cb.has_company_access(company_id))
 WITH CHECK(company_id=cb.authorized_company() AND actor_user_id=cb.authorized_user() AND cb.has_company_access(company_id));
COMMIT;
