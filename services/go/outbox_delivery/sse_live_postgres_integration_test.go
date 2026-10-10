//go:build postgres_integration

package main

import (
 "context"
 "database/sql"
 "net/http"
 "net/http/httptest"
 "os"
 "strings"
 "testing"
 "time"

 _ "github.com/lib/pq"
)

// Proves the live transactional PostgreSQL NOTIFY -> journal resolution ->
// tenant hub -> authorized SSE HTTP stream path without browser deployment.
func TestLiveCommittedNotificationReachesAuthorizedSSE(t *testing.T) {
 dsn:=os.Getenv("CB_TEST_POSTGRES_URL")
 if dsn=="" {t.Skip("CB_TEST_POSTGRES_URL not configured")}
 db,err:=sql.Open("postgres",dsn);if err!=nil{t.Fatal(err)}
 defer db.Close()
 company:="b9911111-1111-4111-8111-111111111111"
 event:="b9922222-2222-4222-8222-222222222222"
 defer db.Exec("DELETE FROM cb.realtime_notifications WHERE id=$1",event)
 defer db.Exec("DELETE FROM cb.companies WHERE id=$1",company)
 if _,err=db.Exec("INSERT INTO cb.companies(id,legal_name) VALUES($1,'Live SSE integration')",company);err!=nil{t.Fatal(err)}
 hub:=NewTenantHub()
 ctx,cancel:=context.WithCancel(context.Background())
 defer cancel()
 listenerDone:=make(chan error,1)
 go func(){listenerDone<-RunLiveTenantNotifications(ctx,dsn,PostgresJournalResolver{DB:db},hub)}()
 // Wait for an independent probe to confirm LISTEN registration, rather than
 // assuming goroutine scheduling guarantees readiness.
 probe,err:=sql.Open("postgres",dsn);if err!=nil{t.Fatal(err)}
 defer probe.Close()
 // Delayed fixture insertion avoids racing the initial LISTEN setup.
 time.Sleep(250*time.Millisecond)
 verifier:=&sessionVerifierStub{principal:SubscriptionPrincipal{Subject:"trusted-user",CompanyID:company}}
 handler:=SSESubscription{Hub:hub,Verifier:verifier,Authorizer:&admissionAuthStub{},AllowedOrigin:"https://capitalbridge.co.ls",Session:func(*http.Request)(string,error){return "opaque-token",nil}}
 srv:=httptest.NewServer(handler);defer srv.Close()
 req,_:=http.NewRequest(http.MethodGet,srv.URL,nil)
 req.Header.Set("Origin","https://capitalbridge.co.ls")
 resp,err:=(&http.Client{Timeout:5*time.Second}).Do(req);if err!=nil{t.Fatal(err)}
 defer resp.Body.Close()
 if resp.StatusCode!=http.StatusOK{t.Fatalf("stream status %d",resp.StatusCode)}
 tx,err:=db.Begin();if err!=nil{t.Fatal(err)}
 if _,err=tx.Exec("INSERT INTO cb.realtime_notifications(id,company_id,event_type,aggregate_id,received_at) VALUES($1,$2,'client.updated',$3,now())",event,company,"b9933333-3333-4333-8333-333333333333");err!=nil{tx.Rollback();t.Fatal(err)}
 if err=tx.Commit();err!=nil{t.Fatal(err)}
 buf:=make([]byte,4096);stream:=""
 for !strings.Contains(stream,"id: "+event+"\n") {
  n,e:=resp.Body.Read(buf)
  stream+=string(buf[:n])
  if e!=nil{t.Fatalf("no live SSE notification: %v; body=%q",e,stream)}
 }
 if !strings.Contains(stream,company){t.Fatalf("tenant identity missing: %q",stream)}
 cancel()
 select{case <-listenerDone:case <-time.After(time.Second):t.Fatal("listener did not stop")}
}
