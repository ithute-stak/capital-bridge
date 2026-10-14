-- Tenant onboarding only through restricted control-plane role.
BEGIN;
CREATE ROLE cb_erp_untrusted_test NOLOGIN NOBYPASSRLS;
GRANT USAGE ON SCHEMA cb TO cb_erp_untrusted_test;
SET LOCAL ROLE cb_erp_untrusted_test;
DO $$
BEGIN
 BEGIN
  PERFORM * FROM cb.register_erp_tenant(
   '22222222-2222-4222-8222-222222222222',
   '11111111-1111-4111-8111-111111111111',
   'Lesotho PostBank','lesotho-postbank','dedicated_stack'
  );
  RAISE EXCEPTION 'untrusted role registered tenant';
 EXCEPTION WHEN insufficient_privilege THEN NULL;
 END;
END $$;
RESET ROLE;
INSERT INTO cb.erp_platform_operators(user_id,active,approved_by) VALUES
 ('22222222-2222-4222-8222-222222222222',true,'33333333-3333-4333-8333-333333333333');
SET LOCAL ROLE cb_erp_control_plane;
SELECT set_config('app.user_id','22222222-2222-4222-8222-222222222222',true);
SELECT tenant_id, tenant_status FROM cb.register_erp_tenant(
 '22222222-2222-4222-8222-222222222222',
 '11111111-1111-4111-8111-111111111111',
 'Lesotho PostBank','lesotho-postbank','dedicated_stack'
);
DO $$
BEGIN
 BEGIN
  PERFORM * FROM cb.register_erp_tenant(
   '22222222-2222-4222-8222-222222222222',
   'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',
   'Bad Company','Invalid Slug','dedicated_stack'
  );
  RAISE EXCEPTION 'invalid slug was accepted';
 EXCEPTION WHEN check_violation OR raise_exception THEN
   IF SQLERRM <> 'Invalid tenant specification' THEN RAISE; END IF;
 END;
END $$;
RESET ROLE;
DO $$
BEGIN
 IF (SELECT COUNT(*) FROM cb.companies WHERE tenant_slug='lesotho-postbank')<>1 THEN
  RAISE EXCEPTION 'expected one tenant';
 END IF;
 IF (SELECT COUNT(*) FROM cb.erp_tenant_admin_audit WHERE action='tenant.registered')<>1 THEN
  RAISE EXCEPTION 'registration audit missing';
 END IF;
END $$;
ROLLBACK;
