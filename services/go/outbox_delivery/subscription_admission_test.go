package main

import (
 "context"
 "errors"
 "testing"
)
type admissionAuthStub struct { err error; calls int }
func (a *admissionAuthStub) AuthorizeSubscription(_ context.Context,_ SubscriptionPrincipal) error { a.calls++; return a.err }
func TestAdmitTenantSubscriptionRequiresAuthorization(t *testing.T) {
 company:="11111111-1111-4111-8111-111111111111"
 p:=SubscriptionPrincipal{Subject:"user-1",CompanyID:company}
 hub:=NewTenantHub()
 ch:=make(chan JournalNotification,1)
 auth:=&admissionAuthStub{err:errors.New("revoked")}
 if _,err:=AdmitTenantSubscription(context.Background(),hub,auth,p,ch);err==nil {t.Fatal("revoked principal admitted")}
 n:=JournalNotification{CompanyID:company}
 if err:=hub.PublishTenant(context.Background(),company,n);err!=nil {t.Fatal(err)}
 select {case <-ch:t.Fatal("unauthorized subscriber received event");default:}
 auth.err=nil
 stop,err:=AdmitTenantSubscription(context.Background(),hub,auth,p,ch)
 if err!=nil {t.Fatal(err)}
 defer stop()
 if err:=hub.PublishTenant(context.Background(),company,n);err!=nil {t.Fatal(err)}
 select {case <-ch:default:t.Fatal("authorized subscriber did not receive event")}
 if _,err:=AdmitTenantSubscription(context.Background(),hub,auth,SubscriptionPrincipal{CompanyID:company},ch);err==nil {t.Fatal("missing subject admitted")}
 if auth.calls!=2 {t.Fatalf("authorization expected twice; got %d",auth.calls)}
}
