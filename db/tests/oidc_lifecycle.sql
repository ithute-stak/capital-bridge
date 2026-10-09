-- Real PostgreSQL login state and session lifecycle checks in disposable CI database.
BEGIN;
INSERT INTO cb.oidc_login_transactions(state_hash,binding_hash,nonce,verifier,created_at,expires_at)
VALUES (repeat('a',64),repeat('b',64),'nonce','verifier',now(),now()+interval '5 minutes');
DO $$
DECLARE first_count integer; second_count integer; wrong_binding integer;
BEGIN
 UPDATE cb.oidc_login_transactions SET consumed_at=now()
  WHERE state_hash=repeat('a',64) AND binding_hash=repeat('c',64)
    AND consumed_at IS NULL AND expires_at>now();
 GET DIAGNOSTICS wrong_binding=ROW_COUNT;
 IF wrong_binding<>0 THEN RAISE EXCEPTION 'Wrong browser binding consumed OIDC transaction'; END IF;
 UPDATE cb.oidc_login_transactions SET consumed_at=now()
  WHERE state_hash=repeat('a',64) AND binding_hash=repeat('b',64)
    AND consumed_at IS NULL AND expires_at>now();
 GET DIAGNOSTICS first_count=ROW_COUNT;
 UPDATE cb.oidc_login_transactions SET consumed_at=now()
  WHERE state_hash=repeat('a',64) AND binding_hash=repeat('b',64)
    AND consumed_at IS NULL AND expires_at>now();
 GET DIAGNOSTICS second_count=ROW_COUNT;
 IF first_count<>1 OR second_count<>0 THEN RAISE EXCEPTION 'OIDC transaction replay permitted'; END IF;
END $$;
INSERT INTO cb.oidc_login_transactions(state_hash,binding_hash,nonce,verifier,created_at,expires_at)
VALUES (repeat('d',64),repeat('e',64),'nonce','verifier',now()-interval '6 minutes',now()-interval '1 minute');
DO $$
DECLARE updated integer;
BEGIN
 UPDATE cb.oidc_login_transactions SET consumed_at=now()
  WHERE state_hash=repeat('d',64) AND binding_hash=repeat('e',64)
    AND consumed_at IS NULL AND expires_at>now();
 GET DIAGNOSTICS updated=ROW_COUNT;
 IF updated<>0 THEN RAISE EXCEPTION 'Expired OIDC state was consumed'; END IF;
END $$;
INSERT INTO cb.user_sessions(key_hash,subject,created_at,expires_at)
VALUES (repeat('f',64),'22222222-2222-4222-8222-222222222222',now(),now()+interval '8 hours');
DO $$
DECLARE revoked integer;
BEGIN
 UPDATE cb.user_sessions SET revoked_at=now()
  WHERE key_hash=repeat('f',64) AND revoked_at IS NULL;
 GET DIAGNOSTICS revoked=ROW_COUNT;
 IF revoked<>1 THEN RAISE EXCEPTION 'Session was not revoked'; END IF;
 IF EXISTS (SELECT 1 FROM cb.user_sessions WHERE key_hash=repeat('f',64)
            AND revoked_at IS NULL AND expires_at>now()) THEN
   RAISE EXCEPTION 'Revoked session remains active';
 END IF;
END $$;
ROLLBACK;
