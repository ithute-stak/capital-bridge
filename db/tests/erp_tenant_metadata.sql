-- Run on disposable database after migration 031. Verifies additive metadata and RLS.
BEGIN;
INSERT INTO cb.companies(id,legal_name,tenant_slug,tenant_status,deployment_mode)
 VALUES
 ('11111111-1111-4111-8111-111111111111','Tenant Alpha','tenant-alpha','active','shared_database'),
 ('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa','Tenant Beta','tenant-beta','suspended','dedicated_stack');
DO $$
BEGIN
 IF (SELECT COUNT(*) FROM cb.companies WHERE tenant_slug IN ('tenant-alpha','tenant-beta'))<>2 THEN
  RAISE EXCEPTION 'Tenant registry entries not created';
 END IF;
 BEGIN
  INSERT INTO cb.companies(id,legal_name,tenant_slug)
   VALUES ('33333333-3333-4333-8333-333333333333','Duplicate','tenant-alpha');
  RAISE EXCEPTION 'Duplicate slug unexpectedly accepted';
 EXCEPTION WHEN unique_violation THEN NULL;
 END;
 BEGIN
  INSERT INTO cb.companies(id,legal_name,tenant_slug)
   VALUES ('44444444-4444-4444-8444-444444444444','Bad slug','Bad Slug');
  RAISE EXCEPTION 'Invalid slug unexpectedly accepted';
 EXCEPTION WHEN check_violation THEN NULL;
 END;
END $$;
CREATE ROLE cb_tenant_metadata_test NOLOGIN NOBYPASSRLS;
GRANT USAGE ON SCHEMA cb TO cb_tenant_metadata_test;
GRANT SELECT ON cb.companies,cb.memberships TO cb_tenant_metadata_test;
GRANT EXECUTE ON FUNCTION cb.has_company_access(uuid) TO cb_tenant_metadata_test;
INSERT INTO cb.memberships(company_id,user_id,role)
 VALUES ('11111111-1111-4111-8111-111111111111','22222222-2222-4222-8222-222222222222','accountant');
SET LOCAL ROLE cb_tenant_metadata_test;
SELECT set_config('app.company_id','11111111-1111-4111-8111-111111111111',true);
SELECT set_config('app.user_id','22222222-2222-4222-8222-222222222222',true);
DO $$
BEGIN
 IF (SELECT COUNT(*) FROM cb.companies)<>1 THEN
  RAISE EXCEPTION 'Tenant registry leaked cross-tenant rows';
 END IF;
END $$;
SELECT set_config('app.company_id','aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',true);
DO $$
BEGIN
 IF EXISTS(SELECT 1 FROM cb.companies) THEN RAISE EXCEPTION 'Forged tenant context leaked rows'; END IF;
END $$;
RESET ROLE;
ROLLBACK;
