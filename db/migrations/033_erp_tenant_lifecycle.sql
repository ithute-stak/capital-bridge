-- Audited tenant state transitions for the isolated CapitalBridge control plane.
BEGIN;
ALTER TABLE cb.erp_tenant_admin_audit DROP CONSTRAINT IF EXISTS erp_tenant_admin_audit_action_check;
ALTER TABLE cb.erp_tenant_admin_audit
 ADD CONSTRAINT erp_tenant_admin_audit_action_check
 CHECK(action IN ('tenant.registered','tenant.activated','tenant.suspended','tenant.retired'));
GRANT UPDATE(tenant_status,provisioned_at) ON cb.companies TO cb_erp_control_plane;
GRANT SELECT(tenant_slug,provisioned_at) ON cb.companies TO cb_erp_control_plane;
-- Existing permissive company RLS policy also evaluates this helper.
GRANT EXECUTE ON FUNCTION cb.has_company_access(uuid) TO cb_erp_control_plane;
CREATE POLICY erp_control_plane_transition ON cb.companies
 FOR UPDATE TO cb_erp_control_plane
 USING(tenant_slug IS NOT NULL)
 WITH CHECK(tenant_slug IS NOT NULL);
-- Control-plane read is limited to tenants with an ERP slug, not their finances.
CREATE POLICY erp_control_plane_metadata_read ON cb.companies
 FOR SELECT TO cb_erp_control_plane USING(tenant_slug IS NOT NULL);
CREATE OR REPLACE FUNCTION cb.transition_erp_tenant(
 p_tenant uuid, p_operator uuid, p_expected text, p_target text
) RETURNS text
LANGUAGE plpgsql SECURITY INVOKER
SET search_path=cb,pg_temp
AS $$
DECLARE current_status text;
BEGIN
 IF NOT pg_has_role(current_user,'cb_erp_control_plane','member') THEN
  RAISE EXCEPTION 'Platform control-plane privilege required' USING ERRCODE='42501';
 END IF;
 IF p_tenant IS NULL OR p_operator IS NULL
 OR p_operator='00000000-0000-0000-0000-000000000000'::uuid
 OR p_expected IS NULL OR p_target IS NULL THEN
  RAISE EXCEPTION 'Invalid tenant transition';
 END IF;
 SELECT tenant_status INTO current_status
 FROM cb.companies WHERE id=p_tenant AND tenant_slug IS NOT NULL FOR UPDATE;
 IF NOT FOUND OR current_status<>p_expected THEN
  RAISE EXCEPTION 'Tenant state conflict';
 END IF;
 IF NOT ((p_expected='pending' AND p_target IN ('active','retired'))
       OR (p_expected='active' AND p_target='suspended')
       OR (p_expected='suspended' AND p_target IN ('active','retired'))) THEN
  RAISE EXCEPTION 'Tenant transition denied';
 END IF;
 UPDATE cb.companies SET tenant_status=p_target,
  provisioned_at=CASE WHEN p_target='active' THEN COALESCE(provisioned_at,now()) ELSE provisioned_at END
  WHERE id=p_tenant;
 INSERT INTO cb.erp_tenant_admin_audit(tenant_id,operator_id,action)
 VALUES(p_tenant,p_operator, 'tenant.' || CASE p_target WHEN 'active' THEN 'activated'
  WHEN 'suspended' THEN 'suspended' ELSE 'retired' END);
 RETURN p_target;
END $$;
REVOKE ALL ON FUNCTION cb.transition_erp_tenant(uuid,uuid,text,text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION cb.transition_erp_tenant(uuid,uuid,text,text) TO cb_erp_control_plane;
COMMIT;
