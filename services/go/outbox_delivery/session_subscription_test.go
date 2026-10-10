package main

import (
 "context"
 "errors"
 "testing"
)
type sessionVerifierStub struct { principal SubscriptionPrincipal; err error; calls int }
func (v *sessionVerifierStub) VerifySubscriptionSession(_ context.Context, _ string) (SubscriptionPrincipal,error) {v.calls++;return v.principal,v.err}
func TestSessionSubscriptionRejectsInvalidAndRevokedSessions(t *testing.T) {
 company:="11111111-1111-4111-8111-111111111111"
 hub:=NewTenantHub()
 ch:=make(chan JournalNotification,1)
 verifier:=&sessionVerifierStub{principal:SubscriptionPrincipal{Subject:"subject-1",CompanyID:company},err:errors.New("revoked")}
 auth:=&admissionAuthStub{}
 if _,err:=AdmitSessionSubscription(context.Background(),hub,verifier,auth,"revoked",ch);err==nil {t.Fatal("revoked session admitted")}
 if auth.calls!=0 {t.Fatal("authorization called after failed verification")}
 verifier.err=nil
 if _,err:=AdmitSessionSubscription(context.Background(),hub,verifier,auth,"",ch);err==nil {t.Fatal("empty session admitted")}
 if verifier.calls!=1 {t.Fatal("empty session reached verifier")}
 stop,err:=AdmitSessionSubscription(context.Background(),hub,verifier,auth,"valid-opaque-token",ch)
 if err!=nil {t.Fatal(err)}
 defer stop()
 if auth.calls!=1 {t.Fatal("authorized session did not reach membership check")}
 if err:=hub.PublishTenant(context.Background(),company,JournalNotification{CompanyID:company});err!=nil {t.Fatal(err)}
 select {case <-ch:default:t.Fatal("verified session did not receive tenant event")}
}
