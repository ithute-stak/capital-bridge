package main
import (
 "bytes"
 "crypto/hmac"
 "crypto/sha256"
 "encoding/hex"
 "net/http"
 "net/http/httptest"
 "strconv"
 "testing"
 "time"
)
type testStore struct { seen map[string]bool }
func (s *testStore) Claim(id string)(bool,error){if s.seen[id]{return false,nil};s.seen[id]=true;return true,nil}
func (s *testStore) ClaimEvent(d Delivery)(bool,error){return s.Claim(d.EventID)}
func TestAuthenticatedIngressAndReplay(t *testing.T){
 key:=[]byte("12345678901234567890123456789012")
 stamp:=time.Unix(1700000000,0)
 store:=&testStore{seen:map[string]bool{}}
 h:=Ingress{Key:key,Store:store,Clock:func()time.Time{return stamp}}
 body:=[]byte(`{"aggregate_id":"invoice-a","company_id":"tenant-a","event_id":"event-a","event_type":"invoice.issued","version":1}`)
 deliver:=func(signature string, when int64)int{
  req:=httptest.NewRequest(http.MethodPost,"/internal/events",bytes.NewReader(body))
  req.Header.Set("Content-Type","application/json")
  req.Header.Set("X-CB-Timestamp",strconv.FormatInt(when,10))
  req.Header.Set("X-CB-Signature",signature)
  recorder:=httptest.NewRecorder();h.ServeHTTP(recorder,req);return recorder.Code
 }
 mac:=hmac.New(sha256.New,key);mac.Write([]byte("1700000000."));mac.Write(body)
 sig:=hex.EncodeToString(mac.Sum(nil))
 if got:=deliver(sig,1700000000);got!=202{t.Fatalf("expected accepted, got %d",got)}
 if got:=deliver(sig,1700000000);got!=200{t.Fatalf("expected idempotent acknowledgement, got %d",got)}
 if got:=deliver("bad",1700000000);got!=401{t.Fatalf("expected signature rejection, got %d",got)}
 if got:=deliver(sig,1699999000);got!=401{t.Fatalf("expected stale rejection, got %d",got)}
}
