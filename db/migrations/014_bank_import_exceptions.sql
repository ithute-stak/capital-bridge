BEGIN;
CREATE TABLE cb.bank_import_exceptions (
 id uuid PRIMARY KEY,
 company_id uuid NOT NULL,
 bank_transaction_id uuid NOT NULL,
 reason text NOT NULL CHECK(reason IN ('missing_reference','amount_mismatch','ambiguous_match','date_outside_window','unmatched')),
 status text NOT NULL DEFAULT 'open' CHECK(status IN ('open','investigating','resolved')),
 notes text NOT NULL DEFAULT '',
 created_at timestamptz NOT NULL DEFAULT now(),
 resolved_by uuid,
 resolved_at timestamptz,
 UNIQUE(company_id,bank_transaction_id),
 FOREIGN KEY(company_id,bank_transaction_id) REFERENCES cb.bank_statement_transactions(company_id,id),
 CHECK ((resolved_by IS NULL AND resolved_at IS NULL) OR (resolved_by IS NOT NULL AND resolved_at IS NOT NULL))
);
ALTER TABLE cb.bank_import_exceptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE cb.bank_import_exceptions FORCE ROW LEVEL SECURITY;
CREATE POLICY bank_import_exception_tenant ON cb.bank_import_exceptions
 USING(company_id=cb.authorized_company() AND cb.has_company_access(company_id))
 WITH CHECK(company_id=cb.authorized_company() AND cb.has_company_access(company_id));
COMMIT;
