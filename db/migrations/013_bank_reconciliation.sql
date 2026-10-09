-- Bank reconciliation evidence foundation. No automatic matching enabled.
BEGIN;
CREATE TABLE cb.bank_statement_transactions (
 id uuid PRIMARY KEY,
 company_id uuid NOT NULL REFERENCES cb.companies(id),
 bank_account_ref text NOT NULL CHECK(length(btrim(bank_account_ref)) BETWEEN 1 AND 80),
 external_transaction_id text NOT NULL CHECK(length(btrim(external_transaction_id)) BETWEEN 1 AND 160),
 transaction_date date NOT NULL,
 description text NOT NULL DEFAULT '',
 amount_minor bigint NOT NULL CHECK(amount_minor<>0),
 currency char(3) NOT NULL DEFAULT 'LSL' CHECK(currency='LSL'),
 imported_at timestamptz NOT NULL DEFAULT now(),
 UNIQUE(company_id,bank_account_ref,external_transaction_id),
 UNIQUE(company_id,id)
);
CREATE TABLE cb.bank_payment_matches (
 id uuid PRIMARY KEY,
 company_id uuid NOT NULL,
 bank_transaction_id uuid NOT NULL,
 payment_id uuid NOT NULL,
 matched_by uuid NOT NULL,
 matched_at timestamptz NOT NULL DEFAULT now(),
 UNIQUE(company_id,bank_transaction_id),
 UNIQUE(company_id,payment_id),
 FOREIGN KEY(company_id,bank_transaction_id) REFERENCES cb.bank_statement_transactions(company_id,id),
 FOREIGN KEY(company_id,payment_id) REFERENCES cb.client_payments(company_id,id)
);
CREATE INDEX bank_tx_company_date ON cb.bank_statement_transactions(company_id,transaction_date DESC);
ALTER TABLE cb.bank_statement_transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE cb.bank_statement_transactions FORCE ROW LEVEL SECURITY;
ALTER TABLE cb.bank_payment_matches ENABLE ROW LEVEL SECURITY;
ALTER TABLE cb.bank_payment_matches FORCE ROW LEVEL SECURITY;
CREATE POLICY bank_transaction_tenant ON cb.bank_statement_transactions
 USING(company_id=cb.authorized_company() AND cb.has_company_access(company_id))
 WITH CHECK(company_id=cb.authorized_company() AND cb.has_company_access(company_id));
CREATE POLICY bank_payment_match_tenant ON cb.bank_payment_matches
 USING(company_id=cb.authorized_company() AND cb.has_company_access(company_id))
 WITH CHECK(company_id=cb.authorized_company() AND matched_by=cb.authorized_user()
 AND cb.has_company_access(company_id));
COMMIT;
