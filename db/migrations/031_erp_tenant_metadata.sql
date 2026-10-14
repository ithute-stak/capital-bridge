-- ERP tenant metadata: existing cb.companies.id is the canonical tenant ID.
-- Additive only: no existing company reassignment or tenant data migration.
BEGIN;
ALTER TABLE cb.companies
 ADD COLUMN IF NOT EXISTS tenant_slug text,
 ADD COLUMN IF NOT EXISTS tenant_status text NOT NULL DEFAULT 'pending',
 ADD COLUMN IF NOT EXISTS deployment_mode text NOT NULL DEFAULT 'shared_database',
 ADD COLUMN IF NOT EXISTS provisioned_at timestamptz;
DO $$
BEGIN
 IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='companies_tenant_slug_format' AND conrelid='cb.companies'::regclass) THEN
  ALTER TABLE cb.companies ADD CONSTRAINT companies_tenant_slug_format
   CHECK(tenant_slug IS NULL OR tenant_slug ~ '^[a-z][a-z0-9-]{2,62}$');
 END IF;
 IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='companies_tenant_status_valid' AND conrelid='cb.companies'::regclass) THEN
  ALTER TABLE cb.companies ADD CONSTRAINT companies_tenant_status_valid
   CHECK(tenant_status IN ('pending','active','suspended','retired'));
 END IF;
 IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='companies_deployment_mode_valid' AND conrelid='cb.companies'::regclass) THEN
  ALTER TABLE cb.companies ADD CONSTRAINT companies_deployment_mode_valid
   CHECK(deployment_mode IN ('shared_database','dedicated_database','dedicated_stack','on_premise'));
 END IF;
END $$;
CREATE UNIQUE INDEX IF NOT EXISTS companies_tenant_slug_unique ON cb.companies(tenant_slug) WHERE tenant_slug IS NOT NULL;
-- Only migration owners may change lifecycle fields; runtime application roles
-- must not receive generic UPDATE privileges on cb.companies.
REVOKE UPDATE ON cb.companies FROM PUBLIC;
COMMIT;
