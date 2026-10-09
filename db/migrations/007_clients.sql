-- Company-scoped CRM foundation. No public write API is enabled by this migration.
BEGIN;
CREATE TABLE cb.clients (
 id uuid PRIMARY KEY,
 company_id uuid NOT NULL REFERENCES cb.companies(id),
 client_code text NOT NULL,
 legal_name text NOT NULL,
 email text,
 phone text,
 status text NOT NULL DEFAULT 'active' CHECK (status IN ('active','inactive')),
 created_at timestamptz NOT NULL DEFAULT now(),
 CHECK (length(btrim(client_code)) BETWEEN 1 AND 40),
 CHECK (length(btrim(legal_name)) BETWEEN 1 AND 250),
 UNIQUE (company_id, client_code),
 UNIQUE (company_id, id)
);
CREATE INDEX clients_company_lookup ON cb.clients(company_id, legal_name, id);
ALTER TABLE cb.clients ENABLE ROW LEVEL SECURITY;
ALTER TABLE cb.clients FORCE ROW LEVEL SECURITY;
CREATE POLICY client_tenant_access ON cb.clients
 USING (
   company_id = nullif(current_setting('app.company_id', true), '')::uuid
   AND EXISTS (
     SELECT 1 FROM cb.memberships m
     WHERE m.company_id = clients.company_id
     AND m.user_id = nullif(current_setting('app.user_id', true), '')::uuid
   )
 )
 WITH CHECK (
   company_id = nullif(current_setting('app.company_id', true), '')::uuid
   AND EXISTS (
     SELECT 1 FROM cb.memberships m
     WHERE m.company_id = clients.company_id
     AND m.user_id = nullif(current_setting('app.user_id', true), '')::uuid
     AND m.role IN ('director','accountant','finance_clerk')
   )
 );
COMMIT;
