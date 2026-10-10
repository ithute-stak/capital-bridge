package main

import (
 "context"
 "testing"
)

func TestRunLiveTenantNotificationsFailsClosed(t *testing.T){
 ctx:=context.Background()
 if err:=RunLiveTenantNotifications(ctx,"",nil,nil);err==nil{t.Fatal("missing dependencies accepted")}
 if err:=RunLiveTenantNotifications(ctx,"postgres://unused",nil,NewTenantHub());err==nil{t.Fatal("missing resolver accepted")}
}
