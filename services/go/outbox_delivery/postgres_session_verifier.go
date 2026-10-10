package main

import (
 "context"
 "crypto/sha256"
 "database/sql"
 "encoding/hex"
 "errors"
)

// PostgresSessionVerifier validates opaque session tokens against the
// server-side session table. Company membership is separately rechecked
// by CompanySubscriptionAuthorizer before hub admission.
type PostgresSessionVerifier struct {
 DB *sql.DB
 // ResolveCompany must be trusted server-side logic: never use client claims.
 ResolveCompany func(context.Context, string) (string, error)
}
func (v PostgresSessionVerifier) VerifySubscriptionSession(ctx context.Context, token string) (SubscriptionPrincipal,error) {
 if v.DB==nil || v.ResolveCompany==nil || len(token)<32 || len(token)>4096 {
  return SubscriptionPrincipal{},errors.New("session verification unavailable")
 }
 hash:=sha256.Sum256([]byte(token))
 var subject string
 err:=v.DB.QueryRowContext(ctx,`
  SELECT subject::text FROM cb.user_sessions
  WHERE key_hash=$1 AND expires_at>now() AND revoked_at IS NULL
 `,hex.EncodeToString(hash[:])).Scan(&subject)
 if err!=nil{return SubscriptionPrincipal{},err}
 company,err:=v.ResolveCompany(ctx,subject)
 if err!=nil{return SubscriptionPrincipal{},err}
 if !signalUUID.MatchString(company) || !signalUUID.MatchString(subject) {
  return SubscriptionPrincipal{},errors.New("invalid verified session identity")
 }
 return SubscriptionPrincipal{Subject:subject,CompanyID:company},nil
}
