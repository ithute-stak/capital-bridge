package main
import (
 "bytes"
 "crypto/hmac"
 "crypto/sha256"
 "encoding/hex"
 "errors"
 "net/http"
 "net/http/httptest"
 "strconv"
 "testing"
 "time"
)
type retryStore struct { calls int; committed bool }
func (s *retryStore) Claim(string)(bool,error){return false,errors.New("legacy not allowed")}
func (s *retryStore) ClaimEvent(d Delivery)(bool,error){
 s.calls++
 if s.calls==1{return false,errors.New("PostgreSQL unavailable")}
 if s.committed{return false,nil}
 s.committed=true
 return true,nil
}
func TestDurableFailureRetriesAndDuplicateAcknowledgement(t *testing.T){
 key:=[]byte("12345678901234567890123456789012")
 timestamp:=time.Unix(1700000000,0)
 store:=&retryStore{}
 handler:=Ingress{Key:key,Store:store,Clock:func()time.Time{return timestamp}}
 body:=[]byte(`{"aggregate_id":"22222222-2222-4222-8222-222222222222","company_id":"33333333-3333-4333-8333-333333333333","event_id":"44444444-4444-4444-8444-444444444444","event_type":"client.updated","version":1}`)
 mac:=hmac.New(sha256.New,key);mac.Write([]byte("1700000000."));mac.Write(body)
 sig:=hex.EncodeToString(mac.Sum(nil))
 send:=func()int{
  req:=httptest.NewRequest(http.MethodPost,"/internal/events",bytes.NewReader(body))
  req.Header.Set("Content-Type","application/json")
  req.Header.Set("X-CB-Timestamp",strconv.FormatInt(timestamp.Unix(),10))
  req.Header.Set("X-CB-Signature",sig)
  w:=httptest.NewRecorder();handler.ServeHTTP(w,req);return w.Code
 }
 if got:=send();got!=503{t.Fatalf("database failure must return 503, got %d",got)}
 if store.committed{t.Fatal("failure must not record delivery")}
 if got:=send();got!=202{t.Fatalf("retry should persist then accept, got %d",got)}
 if got:=send();got!=200{t.Fatalf("durable duplicate should return 200, got %d",got)}
 if store.calls!=3{t.Fatalf("unexpected atomic calls %d",store.calls)}
}
