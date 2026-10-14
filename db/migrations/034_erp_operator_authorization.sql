-- Independently approved CapitalBridge platform operator registry.
-- A UUID passed by an API is never sufficient authorization.
BEGIN;
CREATE TABLE cb.erp_platform_operators (
 user_id uuid PRIMARY KEY,
 active boolean NOT NULL DEFAULT false,
 approved_by uuid NOT NULL,
 approved_at timestamptz NOT NULL DEFAULT now(),
 revoked_at timestamptz,
 CHECK (user_id <> '00000000-0000-0000-0000-000000000000'::uuid),
 CHECK (revoked_at IS NULL OR active=false)
);
REVOKE ALL ON cb.erp_platform_operators FROM PUBLIC;
-- Migration owner must explicitly enroll operators after human verification.
-- No application role receives INSERT/UPDATE/DELETE on this registry.
CREATE OR REPLACE FUNCTION cb.require_erp_platform_operator(p_operator uuid)
RETURNS void LANGUAGE plpgsql SECURITY DEFINER
SET search_path=cb,pg_temp
AS $$
BEGIN
 IF p_operator IS NULL
 OR p_operator IS DISTINCT FROM cb.authorized_user()
 OR NOT EXISTS (
   SELECT 1 FROM cb.erp_platform_operators
   WHERE user_id=p_operator AND active AND revoked_at IS NULL
 ) THEN
  RAISE EXCEPTION 'Verified platform operator required' USING ERRCODE='42501';
 END IF;
END $$;
REVOKE ALL ON FUNCTION cb.require_erp_platform_operator(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION cb.require_erp_platform_operator(uuid) TO cb_erp_control_plane;

-- Reinforce earlier provisioning procedures at DB level.
CREATE OR REPLACE FUNCTION cb.register_erp_tenant(
 p_operator uuid, p_tenant uuid, p_name text, p_slug text, p_mode text
) RETURNS TABLE(tenant_id uuid, tenant_status text)
LANGUAGE plpgsql SECURITY INVOKER SET search_path=cb,pg_temp
AS $$
BEGIN
 IF NOT pg_has_role(current_user,'cb_erp_control_plane','member') THEN
  RAISE EXCEPTION 'Platform control-plane privilege required' USING ERRCODE='42501';
 END IF;
 PERFORM cb.require_erp_platform_operator(p_operator);
 IF p_tenant IS NULL OR p_tenant='00000000-0000-0000-0000-000000000000'::uuid
 OR p_name IS NULL OR length(btrim(p_name))=0 OR length(p_name)>255
 OR p_slug IS NULL OR p_slug !~ '^[a-z][a-z0-9-]{2,62}$'
 OR p_mode NOT IN ('shared_database','dedicated_database','dedicated_stack','on_premise')
 THEN RAISE EXCEPTION 'Invalid tenant specification'; END IF;
 INSERT INTO cb.companies(id,legal_name,tenant_slug,tenant_status,deployment_mode)
 VALUES(p_tenant,btrim(p_name),p_slug,'pending',p_mode);
 INSERT INTO cb.erp_tenant_admin_audit(tenant_id,operator_id,action)
 VALUES(p_tenant,p_operator,'tenant.registered');
 RETURN QUERY SELECT p_tenant,'pending'::text;
END $$;
CREATE OR REPLACE FUNCTION cb.transition_erp_tenant(
 p_tenant uuid, p_operator uuid, p_expected text, p_target text
) RETURNS text LANGUAGE plpgsql SECURITY INVOKER
SET search_path=cb,pg_temp
AS $$
DECLARE current_status text;
BEGIN
 IF NOT pg_has_role(current_user,'cb_erp_control_plane','member') THEN
  RAISE EXCEPTION 'Platform control-plane privilege required' USING ERRCODE='42501';
 END IF;
 PERFORM cb.require_erp_platform_operator(p_operator);
 SELECT tenant_status INTO current_status FROM cb.companies
 WHERE id=p_tenant AND tenant_slug IS NOT NULL FOR UPDATE;
 IF NOT FOUND OR current_status IS DISTINCT FROM p_expected THEN
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
 VALUES(p_tenant,p_operator,'tenant.' || CASE p_target WHEN 'active' THEN 'activated'
 WHEN 'suspended' THEN 'suspended' ELSE 'retired' END);
 RETURN p_target;
END $$;
COMMIT;
