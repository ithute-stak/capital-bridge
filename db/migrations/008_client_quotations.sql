-- Phase 53: Client-linked quotations; no public quotation write API yet.
BEGIN;
CREATE TABLE cb.quotations (
 id uuid PRIMARY KEY,
 company_id uuid NOT NULL REFERENCES cb.companies(id),
 client_id uuid NOT NULL,
 quotation_number text NOT NULL,
 title text NOT NULL,
 currency char(3) NOT NULL DEFAULT 'LSL',
 status text NOT NULL DEFAULT 'draft' CHECK (status IN ('draft','approved','sent','accepted','rejected','expired')),
 issued_on date,
 valid_until date,
 subtotal_minor bigint NOT NULL DEFAULT 0 CHECK(subtotal_minor>=0),
 tax_minor bigint NOT NULL DEFAULT 0 CHECK(tax_minor>=0),
 total_minor bigint GENERATED ALWAYS AS (subtotal_minor + tax_minor) STORED,
 created_at timestamptz NOT NULL DEFAULT now(),
 CHECK(length(btrim(quotation_number)) BETWEEN 1 AND 60),
 CHECK(length(btrim(title)) BETWEEN 1 AND 250),
 CHECK(valid_until IS NULL OR issued_on IS NULL OR valid_until>=issued_on),
 UNIQUE(company_id,quotation_number),
 UNIQUE(company_id,id),
 FOREIGN KEY(company_id,client_id) REFERENCES cb.clients(company_id,id)
);
CREATE TABLE cb.quotation_lines (
 id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
 company_id uuid NOT NULL,
 quotation_id uuid NOT NULL,
 description text NOT NULL CHECK(length(btrim(description)) BETWEEN 1 AND 500),
 quantity integer NOT NULL CHECK(quantity>0),
 unit_price_minor bigint NOT NULL CHECK(unit_price_minor>=0),
 line_total_minor bigint GENERATED ALWAYS AS (quantity * unit_price_minor) STORED,
 FOREIGN KEY(company_id,quotation_id) REFERENCES cb.quotations(company_id,id)
);
CREATE INDEX quotations_company_client ON cb.quotations(company_id,client_id,created_at DESC);
CREATE INDEX quotation_lines_parent ON cb.quotation_lines(company_id,quotation_id);
ALTER TABLE cb.quotations ENABLE ROW LEVEL SECURITY;
ALTER TABLE cb.quotations FORCE ROW LEVEL SECURITY;
ALTER TABLE cb.quotation_lines ENABLE ROW LEVEL SECURITY;
ALTER TABLE cb.quotation_lines FORCE ROW LEVEL SECURITY;
CREATE POLICY quotation_company_access ON cb.quotations
 USING(company_id=cb.authorized_company() AND cb.has_company_access(company_id))
 WITH CHECK(company_id=cb.authorized_company() AND cb.has_company_access(company_id));
CREATE POLICY quotation_lines_company_access ON cb.quotation_lines
 USING(company_id=cb.authorized_company() AND cb.has_company_access(company_id))
 WITH CHECK(company_id=cb.authorized_company() AND cb.has_company_access(company_id));
COMMIT;
