-- Run as the migration owner. Deliberately expose only the current user's memberships.
BEGIN;
CREATE FUNCTION cb.list_my_companies()
RETURNS TABLE(company_id uuid, legal_name text, role text)
LANGUAGE plpgsql STABLE SECURITY DEFINER
SET search_path=cb,pg_temp
AS $$
DECLARE requester uuid;
BEGIN
 requester := cb.authorized_user();
 IF requester IS NULL THEN
  RETURN;
 END IF;
 RETURN QUERY
  SELECT m.company_id, c.legal_name, m.role
  FROM cb.memberships m JOIN cb.companies c ON c.id=m.company_id
  WHERE m.user_id=requester ORDER BY c.legal_name;
END $$;
REVOKE ALL ON FUNCTION cb.list_my_companies() FROM PUBLIC;
-- The deployment administrator must grant EXECUTE only to the restricted
-- runtime role, after provisioning it and confirming it cannot BYPASSRLS.
COMMIT;
