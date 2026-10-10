package main

import (
 "context"
 "testing"
)

func TestTenantHubSignalsOverflowForReplay(t *testing.T) {
 company:="11111111-1111-4111-8111-111111111111"
 other:="22222222-2222-4222-8222-222222222222"
 hub:=NewTenantHub()
 full:=make(chan JournalNotification,1)
 healthy:=make(chan JournalNotification,3)
 stop,err:=hub.RegisterAuthorized(company,full);if err!=nil{t.Fatal(err)}
 defer stop()
 stopHealthy,err:=hub.RegisterAuthorized(other,healthy);if err!=nil{t.Fatal(err)}
 defer stopHealthy()
 overflow:=hub.OverflowSignal(full)
 if overflow==nil{t.Fatal("missing overflow signal")}
 for i:=0;i<2;i++ {
  if err:=hub.PublishTenant(context.Background(),company,JournalNotification{CompanyID:company});err!=nil{t.Fatal(err)}
 }
 select{case <-overflow:default:t.Fatal("dropped event not signaled")}
 select{case <-hub.OverflowSignal(healthy):t.Fatal("other tenant overflowed");default:}
 if len(healthy)!=0{t.Fatal("notification crossed tenant boundary")}
}
