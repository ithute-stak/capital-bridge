-- Invoice data is tenant-scoped. Issuance and ledger posting APIs are NOT enabled.
BEGIN;
CREATE TABLE cb.invoices (
 id uuid PRIMARY KEY,
 company_id uuid NOT NULL REFERENCES cb.companies(id),
 client_id uuid NOT NULL,
 quotation_id uuid,
 invoice_number text NOT NULL,
 issued_on date NOT NULL,
 due_on date NOT NULL,
 currency char(3) NOT NULL DEFAULT 'LSL',
 status text NOT NULL DEFAULT 'draft' CHECK(status IN ('draft','issued','part_paid','paid','void')),
 subtotal_minor bigint NOT NULL CHECK(subtotal_minor>=0),
 tax_minor bigint NOT NULL CHECK(tax_minor>=0),
 total_minor bigint GENERATED ALWAYS AS (subtotal_minor + tax_minor) STORED,
 created_at timestamptz NOT NULL DEFAULT now(),
 CHECK(length(btrim(invoice_number)) BETWEEN 1 AND 60),
 CHECK(due_on>=issued_on),
 UNIQUE(company_id,invoice_number),
 UNIQUE(company_id,id),
 FOREIGN KEY(company_id,client_id) REFERENCES cb.clients(company_id,id),
 FOREIGN KEY(company_id,quotation_id) REFERENCES cb.quotations(company_id,id)
);
CREATE TABLE cb.invoice_lines (
 id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
 company_id uuid NOT NULL,
 invoice_id uuid NOT NULL,
 description text NOT NULL CHECK(length(btrim(description)) BETWEEN 1 AND 500),
 quantity integer NOT NULL CHECK(quantity>0),
 unit_price_minor bigint NOT NULL CHECK(unit_price_minor>=0),
 line_total_minor bigint GENERATED ALWAYS AS (quantity * unit_price_minor) STORED,
 FOREIGN KEY(company_id,invoice_id) REFERENCES cb.invoices(company_id,id)
);
CREATE INDEX invoices_company_client ON cb.invoices(company_id,client_id,issued_on DESC);
CREATE INDEX invoices_company_quotation ON cb.invoices(company_id,quotation_id);
CREATE INDEX invoice_lines_company_invoice ON cb.invoice_lines(company_id,invoice_id);
ALTER TABLE cb.invoices ENABLE ROW LEVEL SECURITY;
ALTER TABLE cb.invoices FORCE ROW LEVEL SECURITY;
ALTER TABLE cb.invoice_lines ENABLE ROW LEVEL SECURITY;
ALTER TABLE cb.invoice_lines FORCE ROW LEVEL SECURITY;
CREATE POLICY invoices_tenant ON cb.invoices
 USING(company_id=cb.authorized_company() AND cb.has_company_access(company_id))
 WITH CHECK(company_id=cb.authorized_company() AND cb.has_company_access(company_id));
CREATE POLICY invoice_lines_tenant ON cb.invoice_lines
 USING(company_id=cb.authorized_company() AND cb.has_company_access(company_id))
 WITH CHECK(company_id=cb.authorized_company() AND cb.has_company_access(company_id));
COMMIT;
