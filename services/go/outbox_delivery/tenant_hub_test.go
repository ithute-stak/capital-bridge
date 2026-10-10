package main

import (
 "context"
 "testing"
)
func TestTenantHubIsolatesCompanies(t *testing.T) {
 h:=NewTenantHub()
 a:="11111111-1111-4111-8111-111111111111"
 b:="22222222-2222-4222-8222-222222222222"
 ca:=make(chan JournalNotification,1)
 cb:=make(chan JournalNotification,1)
 stopA,err:=h.RegisterAuthorized(a,ca);if err!=nil{t.Fatal(err)}
 defer stopA()
 stopB,err:=h.RegisterAuthorized(b,cb);if err!=nil{t.Fatal(err)}
 defer stopB()
 n:=JournalNotification{CompanyID:a,EventID:"33333333-3333-4333-8333-333333333333"}
 if err:=h.PublishTenant(context.Background(),a,n);err!=nil{t.Fatal(err)}
 select{case <-ca:default:t.Fatal("company A did not receive event")}
 select{case <-cb:t.Fatal("company B received foreign event");default:}
 if err:=h.PublishTenant(context.Background(),b,n);err==nil{t.Fatal("cross-tenant publication accepted")}
 stopA()
 if err:=h.PublishTenant(context.Background(),a,n);err!=nil{t.Fatal(err)}
 select{case <-ca:t.Fatal("cancelled subscription received event");default:}
}
