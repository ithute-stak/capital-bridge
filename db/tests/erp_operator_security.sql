-- Security regression: reject operator spoofing, revocation and registry writes.
BEGIN;
INSERT INTO cb.erp_platform_operators(user_id,active,approved_by) VALUES
 ('22222222-2222-4222-8222-222222222222',true,'33333333-3333-4333-8333-333333333333');
SET LOCAL ROLE cb_erp_control_plane;
SELECT set_config('app.user_id','99999999-9999-4999-8999-999999999999',true);
DO $$
BEGIN
 BEGIN
  PERFORM cb.register_erp_tenant(
   '22222222-2222-4222-8222-222222222222',
   '11111111-1111-4111-8111-111111111111',
   'Impersonated Tenant','impersonated-tenant','shared_database');
  RAISE EXCEPTION 'operator impersonation succeeded';
 EXCEPTION WHEN insufficient_privilege THEN NULL;
 END;
 BEGIN
  INSERT INTO cb.erp_platform_operators(user_id,active,approved_by)
  VALUES ('44444444-4444-4444-8444-444444444444',true,'44444444-4444-4444-8444-444444444444');
  RAISE EXCEPTION 'control-plane role enrolled itself';
 EXCEPTION WHEN insufficient_privilege THEN NULL;
 END;
END $$;
RESET ROLE;
UPDATE cb.erp_platform_operators SET active=false,revoked_at=now()
 WHERE user_id='22222222-2222-4222-8222-222222222222';
SET LOCAL ROLE cb_erp_control_plane;
SELECT set_config('app.user_id','22222222-2222-4222-8222-222222222222',true);
DO $$
BEGIN
 BEGIN
  PERFORM cb.register_erp_tenant(
   '22222222-2222-4222-8222-222222222222',
   '11111111-1111-4111-8111-111111111111',
   'Revoked Tenant','revoked-tenant','shared_database');
  RAISE EXCEPTION 'revoked operator registered tenant';
 EXCEPTION WHEN insufficient_privilege THEN NULL;
 END;
END $$;
RESET ROLE;
DO $$
BEGIN
 IF EXISTS(SELECT 1 FROM cb.companies WHERE tenant_slug IN ('impersonated-tenant','revoked-tenant')) THEN
  RAISE EXCEPTION 'unauthorized registration persisted';
 END IF;
END $$;
ROLLBACK;
