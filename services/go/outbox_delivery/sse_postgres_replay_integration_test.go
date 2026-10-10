//go:build postgres_integration

package main

import (
 "context"
 "database/sql"
 "io"
 "net/http"
 "net/http/httptest"
 "os"
 "strings"
 "testing"
 "time"

 _ "github.com/lib/pq"
)

// Exercises committed PostgreSQL journal records through the real replay
// reader and authenticated SSE HTTP handler. Live LISTEN delivery is separate.
func TestCommittedPostgresJournalReplaysThroughSSE(t *testing.T) {
 dsn:=os.Getenv("CB_TEST_POSTGRES_URL")
 if dsn=="" {t.Skip("CB_TEST_POSTGRES_URL not supplied")}
 db,err:=sql.Open("postgres",dsn);if err!=nil{t.Fatal(err)}
 defer db.Close()
 company:="a9911111-1111-4111-8111-111111111111"
 first:="a9922222-2222-4222-8222-222222222222"
 next:="a9933333-3333-4333-8333-333333333333"
 defer func(){
  db.Exec("DELETE FROM cb.realtime_notifications WHERE id IN ($1,$2)",first,next)
  db.Exec("DELETE FROM cb.companies WHERE id=$1",company)
 }()
 if _,err=db.Exec("INSERT INTO cb.companies(id,legal_name) VALUES($1,'SSE replay integration')",company);err!=nil{t.Fatal(err)}
 for _,e:=range []struct{id,ts string}{{first,"2026-02-01T00:00:00Z"},{next,"2026-02-01T00:00:01Z"}}{
  if _,err=db.Exec("INSERT INTO cb.realtime_notifications(id,company_id,event_type,aggregate_id,received_at) VALUES($1,$2,'client.updated',$3,$4::timestamptz)",e.id,company,"a9944444-4444-4444-8444-444444444444",e.ts);err!=nil{t.Fatal(err)}
 }
 verifier:=&sessionVerifierStub{principal:SubscriptionPrincipal{Subject:"trusted-user",CompanyID:company}}
 handler:=SSESubscription{Hub:NewTenantHub(),Replay:PostgresJournalReplay{DB:db},Verifier:verifier,Authorizer:&admissionAuthStub{},AllowedOrigin:"https://capitalbridge.co.ls",Session:func(*http.Request)(string,error){return "opaque-authenticated-token",nil}}
 srv:=httptest.NewServer(handler);defer srv.Close()
 req,_:=http.NewRequestWithContext(context.Background(),http.MethodGet,srv.URL,nil)
 req.Header.Set("Origin","https://capitalbridge.co.ls")
 req.Header.Set("Last-Event-ID",first)
 resp,err:=(&http.Client{Timeout:3*time.Second}).Do(req);if err!=nil{t.Fatal(err)}
 defer resp.Body.Close()
 if resp.StatusCode!=http.StatusOK {t.Fatalf("SSE status %d",resp.StatusCode)}
 buf:=make([]byte,2048)
 var stream string
 for !strings.Contains(stream,"id: "+next+"\n") {
  n,e:=resp.Body.Read(buf);stream+=string(buf[:n])
  if e!=nil {if e==io.EOF{t.Fatalf("replay not delivered: %q",stream)};t.Fatal(e)}
 }
 if !strings.Contains(stream,"event: notification") || !strings.Contains(stream,company){t.Fatalf("invalid tenant replay frame %q",stream)}
}
