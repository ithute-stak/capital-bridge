package main

import (
 "context"
 "errors"
 "io"
 "net/http"
 "net/http/httptest"
 "strings"
 "testing"
 "time"
)
type replayHTTPStub struct { company,cursor string; events []JournalNotification; err error }
func (r *replayHTTPStub) ReplayAfter(_ context.Context,company,cursor string,_ int)([]JournalNotification,error){
 r.company=company;r.cursor=cursor
 return r.events,r.err
}
func TestAuthenticatedSSEReplaysTenantEventOverHTTP(t *testing.T){
 company:="11111111-1111-4111-8111-111111111111"
 cursor:="22222222-2222-4222-8222-222222222222"
 next:="33333333-3333-4333-8333-333333333333"
 replay:=&replayHTTPStub{events:[]JournalNotification{{EventID:next,CompanyID:company}}}
 verifier:=&sessionVerifierStub{principal:SubscriptionPrincipal{Subject:"subject-1",CompanyID:company}}
 handler:=SSESubscription{Hub:NewTenantHub(),Replay:replay,Verifier:verifier,Authorizer:&admissionAuthStub{},AllowedOrigin:"https://capitalbridge.co.ls",Session:func(*http.Request)(string,error){return "opaque-token",nil}}
 srv:=httptest.NewServer(handler);defer srv.Close()
 client:=&http.Client{Timeout:time.Second}
 req,_:=http.NewRequest("GET",srv.URL,nil)
 req.Header.Set("Origin","https://capitalbridge.co.ls")
 req.Header.Set("Last-Event-ID",cursor)
 resp,err:=client.Do(req);if err!=nil{t.Fatal(err)}
 defer resp.Body.Close()
 if resp.StatusCode!=200 {t.Fatalf("unexpected status: %d",resp.StatusCode)}
 b:=make([]byte,2048)
 n,err:=resp.Body.Read(b);if err!=nil&&err!=io.EOF{t.Fatal(err)}
 // The first read may capture only the initial flush. Continue until replay frame arrives.
 stream:=string(b[:n])
 for !strings.Contains(stream,"id: "+next) {
  n,err=resp.Body.Read(b);if err!=nil{t.Fatalf("replay frame missing: %v",err)}
  stream+=string(b[:n])
 }
 if replay.company!=company||replay.cursor!=cursor{t.Fatalf("replay scope mismatch: %+v",replay)}
 if !strings.Contains(stream,"event: notification"){t.Fatalf("missing notification frame: %q",stream)}
}
func TestAuthenticatedSSERejectsReplayFailure(t *testing.T){
 company:="11111111-1111-4111-8111-111111111111"
 replay:=&replayHTTPStub{err:errors.New("offline")}
 handler:=SSESubscription{Hub:NewTenantHub(),Replay:replay,Verifier:&sessionVerifierStub{principal:SubscriptionPrincipal{Subject:"subject-1",CompanyID:company}},Authorizer:&admissionAuthStub{},AllowedOrigin:"https://capitalbridge.co.ls",Session:func(*http.Request)(string,error){return "token",nil}}
 w:=httptest.NewRecorder()
 req:=httptest.NewRequest("GET","/events",nil)
 req.Header.Set("Origin","https://capitalbridge.co.ls")
 req.Header.Set("Last-Event-ID","22222222-2222-4222-8222-222222222222")
 handler.ServeHTTP(w,req)
 if w.Code!=http.StatusConflict{t.Fatalf("expected conflict, got %d",w.Code)}
}
