-- Verify tenant access when one restricted database connection serves sequential users.
-- Runs against disposable CI PostgreSQL only.
BEGIN;
CREATE ROLE cb_tenant_switch_test NOLOGIN NOBYPASSRLS;
GRANT USAGE ON SCHEMA cb TO cb_tenant_switch_test;
GRANT SELECT ON cb.companies, cb.memberships, cb.accounts TO cb_tenant_switch_test;
GRANT EXECUTE ON FUNCTION cb.has_company_access(uuid) TO cb_tenant_switch_test;

INSERT INTO cb.companies(id,legal_name) VALUES
 ('11111111-1111-4111-8111-111111111111','Switch A'),
 ('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa','Switch B');
INSERT INTO cb.memberships(company_id,user_id,role) VALUES
 ('11111111-1111-4111-8111-111111111111','22222222-2222-4222-8222-222222222222','accountant'),
 ('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa','bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb','accountant');
INSERT INTO cb.accounts(company_id,code,name,kind) VALUES
 ('11111111-1111-4111-8111-111111111111','1000','Bank A','asset'),
 ('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa','1000','Bank B','asset');
SET LOCAL ROLE cb_tenant_switch_test;

SELECT set_config('app.company_id','11111111-1111-4111-8111-111111111111',true);
SELECT set_config('app.user_id','22222222-2222-4222-8222-222222222222',true);
DO $$
BEGIN
 IF (SELECT count(*) FROM cb.accounts)<>1 OR (SELECT min(name) FROM cb.accounts)<>'Bank A' THEN
  RAISE EXCEPTION 'Company A account isolation failed';
 END IF;
END $$;

-- Switch company context without switching the authenticated user.
SELECT set_config('app.company_id','aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',true);
DO $$
BEGIN
 IF EXISTS (SELECT 1 FROM cb.accounts) THEN
  RAISE EXCEPTION 'Company B accessible to user A';
 END IF;
END $$;

-- A separately validated user B can access only company B records.
SELECT set_config('app.user_id','bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb',true);
DO $$
BEGIN
 IF (SELECT count(*) FROM cb.accounts)<>1 OR (SELECT min(name) FROM cb.accounts)<>'Bank B' THEN
  RAISE EXCEPTION 'Company B account isolation failed';
 END IF;
END $$;

-- A user B identity cannot read A by changing the company identifier.
SELECT set_config('app.company_id','11111111-1111-4111-8111-111111111111',true);
DO $$
BEGIN
 IF EXISTS (SELECT 1 FROM cb.accounts) THEN
  RAISE EXCEPTION 'Company A accessible to user B';
 END IF;
END $$;

-- Database transaction closure clears all transaction-local RLS context.
RESET ROLE;
ROLLBACK;
