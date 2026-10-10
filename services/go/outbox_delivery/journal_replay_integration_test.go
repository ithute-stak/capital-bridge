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

func TestTenantJournalReplayAgainstPostgres(t *testing.T) {
 dsn:=os.Getenv("CB_TEST_POSTGRES_URL");if dsn==""{t.Skip("CB_TEST_POSTGRES_URL not supplied")}
 db,err:=sql.Open("postgres",dsn);if err!=nil{t.Fatal(err)}
 a:="1111aaaa-1111-4111-8111-111111111111"
 b:="2222bbbb-2222-4222-8222-222222222222"
 first:="3333cccc-3333-4333-8333-333333333333"
 second:="4444dddd-4444-4444-8444-444444444444"
 foreign:="5555eeee-5555-4555-8555-555555555555"
 t.Cleanup(func() {
  for _,id:=range []string{first,second,foreign}{if _,e:=db.Exec("DELETE FROM cb.realtime_notifications WHERE id=$1",id);e!=nil{t.Error(e)}}
  for _,id:=range []string{a,b}{if _,e:=db.Exec("DELETE FROM cb.companies WHERE id=$1",id);e!=nil{t.Error(e)}}
  db.Close()
 })
 for _,id:=range []string{a,b}{if _,e:=db.Exec("INSERT INTO cb.companies(id,legal_name) VALUES($1,'Replay test')",id);e!=nil{t.Fatal(e)}}
 for i,v:=range []struct{id,company,received string}{
  {first,a,"2026-01-01T00:00:00Z"},{second,a,"2026-01-01T00:00:01Z"},{foreign,b,"2026-01-01T00:00:02Z"},
 } {
  if _,e:=db.Exec("INSERT INTO cb.realtime_notifications(id,company_id,event_type,aggregate_id,received_at) VALUES($1,$2,'client.updated',$3,$4::timestamptz)",v.id,v.company,"6666ffff-6666-4666-8666-666666666666",v.received);e!=nil{t.Fatalf("insert %d: %v",i,e)}
 }
 replay:=PostgresJournalReplay{DB:db}
 events,err:=replay.ReplayAfter(context.Background(),a,first,10)
 if err!=nil{t.Fatal(err)}
 if len(events)!=1||events[0].EventID!=second||events[0].CompanyID!=a{t.Fatalf("unexpected replay: %+v",events)}
 if _,err:=replay.ReplayAfter(context.Background(),a,foreign,10);!errors.Is(err,sql.ErrNoRows){t.Fatalf("foreign cursor should be rejected: %v",err)}
 if _,err:=replay.ReplayAfter(context.Background(),a,first,101);err==nil{t.Fatal("unbounded replay accepted")}
}
