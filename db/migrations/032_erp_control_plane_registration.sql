-- Platform control-plane registry procedure. Not exposed to finance runtime.
-- Apply as migration owner after migration 031.
BEGIN;
CREATE TABLE IF NOT EXISTS cb.erp_tenant_admin_audit (
 id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
 tenant_id uuid NOT NULL REFERENCES cb.companies(id),
 operator_id uuid NOT NULL,
 action text NOT NULL CHECK(action IN ('tenant.registered')),
 recorded_at timestamptz NOT NULL DEFAULT now()
);
REVOKE ALL ON cb.erp_tenant_admin_audit FROM PUBLIC;

-- A dedicated NOLOGIN group role is granted ONLY to the authenticated
-- control-plane DB login after operator identity and operational review.
DO $$
BEGIN
 IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='cb_erp_control_plane') THEN
  CREATE ROLE cb_erp_control_plane NOLOGIN NOBYPASSRLS;
 END IF;
END $$;
GRANT USAGE ON SCHEMA cb TO cb_erp_control_plane;
GRANT INSERT(id,legal_name,tenant_slug,tenant_status,deployment_mode)
 ON cb.companies TO cb_erp_control_plane;
GRANT INSERT(tenant_id,operator_id,action)
 ON cb.erp_tenant_admin_audit TO cb_erp_control_plane;
GRANT SELECT(id,tenant_status) ON cb.companies TO cb_erp_control_plane;
-- No membership, ledger, user-session or finance table privileges granted.

CREATE OR REPLACE FUNCTION cb.register_erp_tenant(
 p_operator uuid, p_tenant uuid, p_name text, p_slug text, p_mode text
) RETURNS TABLE(tenant_id uuid, tenant_status text)
LANGUAGE plpgsql SECURITY INVOKER
SET search_path=cb,pg_temp
AS $$
BEGIN
 IF NOT pg_has_role(current_user, 'cb_erp_control_plane', 'member') THEN
  RAISE EXCEPTION 'Platform control-plane privilege required' USING ERRCODE='42501';
 END IF;
 IF p_operator IS NULL OR p_operator='00000000-0000-0000-0000-000000000000'::uuid
 OR p_tenant IS NULL OR p_tenant='00000000-0000-0000-0000-000000000000'::uuid
 OR p_name IS NULL OR length(btrim(p_name))=0 OR length(p_name)>255
 OR p_slug IS NULL OR p_slug !~ '^[a-z][a-z0-9-]{2,62}$'
 OR p_mode NOT IN ('shared_database','dedicated_database','dedicated_stack','on_premise')
 THEN RAISE EXCEPTION 'Invalid tenant specification'; END IF;

 -- RLS is forced for cb.companies. The dedicated control-plane role gets
 -- insert-only policy with pending status, and SELECT access only to the
 -- just-registered tenant through the returned values below.
 INSERT INTO cb.companies(id,legal_name,tenant_slug,tenant_status,deployment_mode)
 VALUES(p_tenant,btrim(p_name),p_slug,'pending',p_mode);
 INSERT INTO cb.erp_tenant_admin_audit(tenant_id,operator_id,action)
 VALUES(p_tenant,p_operator,'tenant.registered');
 RETURN QUERY SELECT p_tenant,'pending'::text;
END $$;
REVOKE ALL ON FUNCTION cb.register_erp_tenant(uuid,uuid,text,text,text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION cb.register_erp_tenant(uuid,uuid,text,text,text) TO cb_erp_control_plane;
CREATE POLICY erp_control_plane_register_pending ON cb.companies FOR INSERT
 TO cb_erp_control_plane
 WITH CHECK(tenant_status='pending' AND provisioned_at IS NULL AND tenant_slug IS NOT NULL);
COMMIT;
