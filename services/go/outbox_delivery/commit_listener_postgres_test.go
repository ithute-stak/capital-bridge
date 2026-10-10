//go:build postgres_integration

package main

import (
 "context"
 "database/sql"
 "encoding/json"
 "os"
 "testing"
 "time"

 _ "github.com/lib/pq"
)

// Exercise a real LISTEN/NOTIFY delivery from a committed PostgreSQL journal
// row. This does not claim browser broadcast or service startup integration.
func TestCommitListenerReceivesPostgresNotification(t *testing.T) {
 dsn:=os.Getenv("CB_TEST_POSTGRES_URL")
 if dsn=="" {t.Skip("CB_TEST_POSTGRES_URL not supplied")}
 db,err:=sql.Open("postgres",dsn);if err!=nil {t.Fatal(err)}
 defer db.Close()
 company:="a1111111-1111-4111-8111-111111111111"
 event:="a2222222-2222-4222-8222-222222222222"
 _,err=db.Exec("INSERT INTO cb.companies(id,legal_name) VALUES($1,'Listener test') ON CONFLICT(id) DO NOTHING",company)
 if err!=nil {t.Fatal(err)}
 t.Cleanup(func(){
  db.Exec("DELETE FROM cb.realtime_notifications WHERE id=$1",event)
  db.Exec("DELETE FROM cb.companies WHERE id=$1",company)
 })
 ctx,cancel:=context.WithTimeout(context.Background(),8*time.Second)
 defer cancel()
 received:=make(chan CommitSignal,1)
 done:=make(chan error,1)
 go func(){done<-ListenCommitSignals(ctx,dsn,func(_ context.Context,s CommitSignal)error{
  select {case received<-s:default:}
  return nil
 })}()
 // Wait until LISTEN is registered before publishing. A lost NOTIFY would
 // otherwise be expected and is precisely why journal replay is required.
 ready:=false
 for i:=0;i<40;i++ {
  var count int
  if e:=db.QueryRow("SELECT COUNT(*) FROM pg_stat_activity WHERE query LIKE 'LISTEN cb_realtime_events%' AND state='idle'").Scan(&count);e==nil && count>0 {ready=true;break}
  select {case err:=<-done:t.Fatalf("listener exited early: %v",err);case <-time.After(50*time.Millisecond):}
 }
 if !ready {t.Fatal("LISTEN subscription did not become ready")}
 _,err=db.Exec("INSERT INTO cb.realtime_notifications(id,company_id,event_type,aggregate_id) VALUES($1,$2,'client.updated',$3)",event,company,"a3333333-3333-4333-8333-333333333333")
 if err!=nil {t.Fatal(err)}
 select {
 case signal:=<-received:
  if signal.CompanyID!=company || signal.EventID!=event {b,_:=json.Marshal(signal);t.Fatalf("wrong hint %s",b)}
 case <-ctx.Done():t.Fatal("no notification received before timeout")
 }
 cancel()
 select {case <-done:case <-time.After(time.Second):t.Fatal("listener did not stop on cancellation")}
}
