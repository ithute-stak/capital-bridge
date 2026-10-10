package main

import (
 "context"
 "testing"
)
func TestJournalResolverFailsClosedWithoutDatabase(t *testing.T){
 hint:=CommitSignal{CompanyID:"11111111-1111-4111-8111-111111111111",EventID:"22222222-2222-4222-8222-222222222222"}
 if _,err:=(PostgresJournalResolver{}).ResolveNotification(context.Background(),hint);err==nil {t.Fatal("nil DB accepted")}
}
