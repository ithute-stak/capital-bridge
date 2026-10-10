//go:build postgres_integration

package main

import (
 "context"
 "crypto/sha256"
 "database/sql"
 "encoding/hex"
 "errors"
 "os"
 "testing"
 "time"
 _ "github.com/lib/pq"
)

func TestPostgresSubscriptionSessionLifecycle(t *testing.T) {
 dsn:=os.Getenv("CB_TEST_POSTGRES_URL")
 if dsn=="" {t.Skip("CB_TEST_POSTGRES_URL not supplied")}
 db,err:=sql.Open("postgres",dsn);if err!=nil{t.Fatal(err)}
 defer db.Close()
 subject:="c1111111-1111-4111-8111-111111111111"
 company:="c2222222-2222-4222-8222-222222222222"
 token:="integration-session-token-12345678901234567890"
 hash:=sha256.Sum256([]byte(token))
 key:=hex.EncodeToString(hash[:])
 defer db.Exec("DELETE FROM cb.user_sessions WHERE key_hash=$1",key)
 verifier:=PostgresSessionVerifier{DB:db,ResolveCompany:func(_ context.Context,s string)(string,error){
  if s!=subject{return "",errors.New("wrong subject")}
  return company,nil
 }}
 insert:=func(expired bool) {
  t.Helper()
  expiry:=time.Now().Add(time.Hour)
  if expired {expiry=time.Now().Add(-time.Hour)}
  if _,err:=db.Exec(`INSERT INTO cb.user_sessions(key_hash,subject,created_at,expires_at) VALUES($1,$2,$3,$4)`,key,subject,time.Now().Add(-2*time.Hour),expiry);err!=nil{t.Fatal(err)}
 }
 insert(false)
 p,err:=verifier.VerifySubscriptionSession(context.Background(),token)
 if err!=nil || p.Subject!=subject || p.CompanyID!=company{t.Fatalf("valid session: %+v %v",p,err)}
 if _,err:=db.Exec("UPDATE cb.user_sessions SET revoked_at=now() WHERE key_hash=$1",key);err!=nil{t.Fatal(err)}
 if _,err:=verifier.VerifySubscriptionSession(context.Background(),token);!errors.Is(err,sql.ErrNoRows){t.Fatalf("revoked session accepted: %v",err)}
 if _,err:=db.Exec("DELETE FROM cb.user_sessions WHERE key_hash=$1",key);err!=nil{t.Fatal(err)}
 insert(true)
 if _,err:=verifier.VerifySubscriptionSession(context.Background(),token);!errors.Is(err,sql.ErrNoRows){t.Fatalf("expired session accepted: %v",err)}
}
