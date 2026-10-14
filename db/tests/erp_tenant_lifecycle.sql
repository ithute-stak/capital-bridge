-- Disposable CI DB: registration then state transitions are audited and restricted.
BEGIN;
SET LOCAL ROLE cb_erp_control_plane;
SELECT cb.register_erp_tenant(
 '22222222-2222-4222-8222-222222222222',
 '11111111-1111-4111-8111-111111111111',
 'Bank Test','bank-test','dedicated_stack');
DO $$
DECLARE next_status text;
BEGIN
 next_status := cb.transition_erp_tenant(
 '11111111-1111-4111-8111-111111111111',
 '22222222-2222-4222-8222-222222222222','pending','active');
 IF next_status <> 'active' THEN RAISE EXCEPTION 'activation failed'; END IF;
 BEGIN
  PERFORM cb.transition_erp_tenant(
   '11111111-1111-4111-8111-111111111111',
   '22222222-2222-4222-8222-222222222222','pending','retired');
  RAISE EXCEPTION 'stale state transition succeeded';
 EXCEPTION WHEN raise_exception THEN
  IF SQLERRM <> 'Tenant state conflict' THEN RAISE; END IF;
 END;
 PERFORM cb.transition_erp_tenant(
   '11111111-1111-4111-8111-111111111111',
   '22222222-2222-4222-8222-222222222222','active','suspended');
END $$;
RESET ROLE;
DO $$
BEGIN
 IF (SELECT tenant_status FROM cb.companies WHERE tenant_slug='bank-test')<>'suspended' THEN
  RAISE EXCEPTION 'tenant not suspended';
 END IF;
 IF (SELECT count(*) FROM cb.erp_tenant_admin_audit
      WHERE tenant_id='11111111-1111-4111-8111-111111111111')<>3 THEN
  RAISE EXCEPTION 'tenant audit chain missing';
 END IF;
END $$;
ROLLBACK;
