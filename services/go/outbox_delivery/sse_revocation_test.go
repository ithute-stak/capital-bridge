package main

import (
 "context"
 "errors"
 "net/http"
 "net/http/httptest"
 "sync"
 "testing"
 "time"
)

type revocableSessionVerifier struct {mu sync.Mutex; revoked bool; calls int; principal SubscriptionPrincipal}
func (v *revocableSessionVerifier) VerifySubscriptionSession(_ context.Context,_ string)(SubscriptionPrincipal,error){
 v.mu.Lock();defer v.mu.Unlock();v.calls++
 if v.revoked{return SubscriptionPrincipal{},errors.New("revoked")}
 return v.principal,nil
}
func TestSSEClosesAfterSessionRevocation(t *testing.T){
 company:="11111111-1111-4111-8111-111111111111"
 v:=&revocableSessionVerifier{principal:SubscriptionPrincipal{Subject:"subject-1",CompanyID:company}}
 auth:=&admissionAuthStub{}
 handler:=SSESubscription{Hub:NewTenantHub(),Verifier:v,Authorizer:auth,AllowedOrigin:"https://capitalbridge.co.ls",RevalidateInterval:10*time.Millisecond,Session:func(*http.Request)(string,error){return "opaque-session-token",nil}}
 server:=httptest.NewServer(handler);defer server.Close()
 req,err:=http.NewRequest(http.MethodGet,server.URL,nil);if err!=nil{t.Fatal(err)}
 req.Header.Set("Origin","https://capitalbridge.co.ls")
 client:=&http.Client{Timeout:time.Second}
 resp,err:=client.Do(req);if err!=nil{t.Fatal(err)}
 defer resp.Body.Close()
 if resp.StatusCode!=http.StatusOK{t.Fatalf("stream returned %d",resp.StatusCode)}
 v.mu.Lock();v.revoked=true;v.mu.Unlock()
 ended:=make(chan error,1)
 go func(){buffer:=make([]byte,32);for{_,err:=resp.Body.Read(buffer);if err!=nil{ended<-err;return}}}()
 select{case <-ended:case <-time.After(500*time.Millisecond):t.Fatal("revoked SSE session remained connected")}
}
