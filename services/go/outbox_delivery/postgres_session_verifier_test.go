package main

import (
 "context"
 "testing"
)
func TestPostgresSessionVerifierFailsClosed(t *testing.T) {
 v:=PostgresSessionVerifier{}
 for _,token:=range []string{"", "short", "12345678901234567890123456789012"} {
  if _,err:=v.VerifySubscriptionSession(context.Background(),token);err==nil {t.Fatalf("unconfigured verifier accepted token length %d",len(token))}
 }
}
