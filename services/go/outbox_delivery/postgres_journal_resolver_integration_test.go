//go:build postgres_integration

package main

import (
 "context"
 "database/sql"
 "errors"
 "os"
 "testing"

 _ "github.com/lib/pq"
)

// TestJournalResolverMatchesCompanyAndEvent proves the resolver uses both
// identifiers and does not return a row belonging to another company.
func TestJournalResolverMatchesCompanyAndEvent(t *testing.T) {
 dsn:=os.Getenv("CB_TEST_POSTGRES_URL")
 if dsn=="" {t.Skip("CB_TEST_POSTGRES_URL not supplied")}
 db,err:=sql.Open("postgres",dsn);if err!=nil {t.Fatal(err)}
 companyA:="b1111111-1111-4111-8111-111111111111"
 companyB:="b2222222-2222-4222-8222-222222222222"
 event:="b3333333-3333-4333-8333-333333333333"
 t.Cleanup(func(){
  if _,err:=db.Exec("DELETE FROM cb.realtime_notifications WHERE id=$1",event);err!=nil{t.Error(err)}
  for _,c:=range []string{companyA,companyB}{
   if _,err:=db.Exec("DELETE FROM cb.companies WHERE id=$1",c);err!=nil{t.Error(err)}
  }
  db.Close()
 })
 for _,c:=range []string{companyA,companyB}{
  if _,err:=db.Exec("INSERT INTO cb.companies(id,legal_name) VALUES($1,'Resolver integration test')",c);err!=nil{t.Fatal(err)}
 }
 if _,err:=db.Exec("INSERT INTO cb.realtime_notifications(id,company_id,event_type,aggregate_id) VALUES($1,$2,'client.updated',$3)",event,companyA,"b4444444-4444-4444-8444-444444444444");err!=nil{t.Fatal(err)}
 resolver:=PostgresJournalResolver{DB:db}
 ctx:=context.Background()
 good:=CommitSignal{CompanyID:companyA,EventID:event}
 n,err:=resolver.ResolveNotification(ctx,good)
 if err!=nil{t.Fatal(err)}
 if n.CompanyID!=companyA || n.EventID!=event || n.EventType!="client.updated"{t.Fatalf("wrong resolved notification: %+v",n)}
 foreign:=CommitSignal{CompanyID:companyB,EventID:event}
 if _,err:=resolver.ResolveNotification(ctx,foreign);!errors.Is(err,sql.ErrNoRows){t.Fatalf("foreign company must see no rows, got %v",err)}
}
