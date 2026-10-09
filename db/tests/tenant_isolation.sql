-- Tenant boundary smoke test. Executes only in the disposable CI database.
-- The untrusted tenant context is set via the trusted application session for test.
BEGIN;
CREATE ROLE cb_runtime_test NOLOGIN NOBYPASSRLS;
GRANT USAGE ON SCHEMA cb TO cb_runtime_test;
GRANT SELECT ON cb.companies,cb.memberships,cb.accounts,cb.periods,
  cb.journals,cb.journal_lines TO cb_runtime_test;
GRANT EXECUTE ON FUNCTION cb.has_company_access(uuid) TO cb_runtime_test;

INSERT INTO cb.companies(id,legal_name) VALUES
 ('11111111-1111-4111-8111-111111111111','Company A'),
 ('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa','Company B');
INSERT INTO cb.memberships(company_id,user_id,role) VALUES
 ('11111111-1111-4111-8111-111111111111',
  '22222222-2222-4222-8222-222222222222','accountant'),
 ('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',
  'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb','accountant');
INSERT INTO cb.accounts(company_id,code,name,kind) VALUES
 ('11111111-1111-4111-8111-111111111111','1000','A bank','asset'),
 ('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa','1000','B bank','asset');

SET LOCAL ROLE cb_runtime_test;
SELECT set_config('app.company_id','11111111-1111-4111-8111-111111111111',true);
SELECT set_config('app.user_id','22222222-2222-4222-8222-222222222222',true);
DO $$
BEGIN
 IF (SELECT count(*) FROM cb.accounts) <> 1 THEN
  RAISE EXCEPTION 'Company A must see only its own accounts';
 END IF;
 IF (SELECT count(*) FROM cb.companies) <> 1 THEN
  RAISE EXCEPTION 'Company A must see only itself';
 END IF;
 IF (SELECT count(*) FROM cb.memberships) <> 1 THEN
  RAISE EXCEPTION 'Company A membership policy leaks rows';
 END IF;
END $$;

-- Forging only the tenant identifier cannot grant access to company B.
SELECT set_config('app.company_id','aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',true);
DO $$
BEGIN
 IF EXISTS(SELECT 1 FROM cb.accounts) OR EXISTS(SELECT 1 FROM cb.companies) THEN
  RAISE EXCEPTION 'Cross-tenant access possible through company context alone';
 END IF;
END $$;

-- The runtime account must not have DML rights.
DO $$
BEGIN
 BEGIN
  INSERT INTO cb.accounts(company_id,code,name,kind)
   VALUES ('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa','9999','Attack','asset');
  RAISE EXCEPTION 'expected write permission failure';
 EXCEPTION WHEN insufficient_privilege THEN NULL;
 END;
END $$;

-- Unset identity must return zero rows (fail closed).
SELECT set_config('app.company_id','',true);
SELECT set_config('app.user_id','',true);
DO $$
BEGIN
 IF EXISTS(SELECT 1 FROM cb.accounts) OR EXISTS(SELECT 1 FROM cb.companies) THEN
  RAISE EXCEPTION 'Unset context exposed financial rows';
 END IF;
END $$;
RESET ROLE;
ROLLBACK;
