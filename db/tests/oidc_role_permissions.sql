-- Verify authentication roles have only their intended table privileges.
DO $$
DECLARE role_name text; table_name text; privilege text; allowed boolean;
BEGIN
 FOREACH role_name IN ARRAY ARRAY['cb_oidc_transactions','cb_oidc_identities','cb_oidc_sessions'] LOOP
  IF (SELECT rolcanlogin OR rolbypassrls OR rolsuper OR rolcreaterole OR rolcreatedb
      FROM pg_roles WHERE rolname=role_name) THEN
   RAISE EXCEPTION 'Excessive role capabilities: %',role_name;
  END IF;
  FOREACH table_name IN ARRAY ARRAY['oidc_login_transactions','external_identities','user_sessions','accounts','journals'] LOOP
   FOREACH privilege IN ARRAY ARRAY['SELECT','INSERT','UPDATE','DELETE','TRUNCATE','REFERENCES','TRIGGER'] LOOP
    allowed := (role_name='cb_oidc_transactions' AND table_name='oidc_login_transactions' AND privilege IN ('SELECT','INSERT','UPDATE','DELETE'))
      OR (role_name='cb_oidc_identities' AND table_name='external_identities' AND privilege='SELECT')
      OR (role_name='cb_oidc_sessions' AND table_name='user_sessions' AND privilege IN ('SELECT','INSERT','UPDATE','DELETE'));
    IF has_table_privilege(role_name,'cb.'||table_name,privilege) <> allowed THEN
     RAISE EXCEPTION 'Unexpected privilege % % %',role_name,table_name,privilege;
    END IF;
   END LOOP;
  END LOOP;
 END LOOP;
END $$;
