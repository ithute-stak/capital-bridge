-- End-to-end checks under real SET ROLE (test database only).
BEGIN;
DO $$
BEGIN
 IF has_table_privilege('cb_oidc_identities','cb.user_sessions','SELECT') THEN
   RAISE EXCEPTION 'Identity role can access session tokens';
 END IF;
 IF has_table_privilege('cb_oidc_sessions','cb.external_identities','SELECT') THEN
   RAISE EXCEPTION 'Session role can access identity mappings';
 END IF;
END $$;
SET LOCAL ROLE cb_oidc_identities;
DO $$
BEGIN
 IF CURRENT_USER <> 'cb_oidc_identities' THEN
  RAISE EXCEPTION 'Wrong active role';
 END IF;
 BEGIN
  INSERT INTO cb.external_identities(issuer,subject,user_id)
  VALUES ('https://id.example','attacker','22222222-2222-4222-8222-222222222222');
  RAISE EXCEPTION 'Identity role was allowed to write';
 EXCEPTION WHEN insufficient_privilege THEN NULL;
 END;
 BEGIN
  PERFORM * FROM cb.user_sessions;
  RAISE EXCEPTION 'Identity role was allowed to read sessions';
 EXCEPTION WHEN insufficient_privilege THEN NULL;
 END;
END $$;
RESET ROLE;
SET LOCAL ROLE cb_oidc_transactions;
DO $$
BEGIN
 IF CURRENT_USER <> 'cb_oidc_transactions' THEN
  RAISE EXCEPTION 'Wrong transaction role';
 END IF;
 BEGIN
  PERFORM * FROM cb.external_identities;
  RAISE EXCEPTION 'Transaction role was allowed to read identities';
 EXCEPTION WHEN insufficient_privilege THEN NULL;
 END;
END $$;
RESET ROLE;
SET LOCAL ROLE cb_oidc_sessions;
DO $$
BEGIN
 IF CURRENT_USER <> 'cb_oidc_sessions' THEN
  RAISE EXCEPTION 'Wrong session role';
 END IF;
 BEGIN
  PERFORM * FROM cb.journals;
  RAISE EXCEPTION 'Session role was allowed to read financial journals';
 EXCEPTION WHEN insufficient_privilege THEN NULL;
 END;
END $$;
RESET ROLE;
ROLLBACK;
