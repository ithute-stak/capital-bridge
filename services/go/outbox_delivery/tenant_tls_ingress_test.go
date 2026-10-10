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

// tenantScopedTestStore verifies that the handler rejects a cross-tenant
// event before invoking the durable persistence operation.
type tenantScopedTestStore struct {
 company string
 claims int
 seen map[string]bool
}
func (s *tenantScopedTestStore) AllowedCompany() string { return s.company }
func (s *tenantScopedTestStore) Claim(id string) (bool,error) {
 if s.seen[id] { return false,nil }
 s.seen[id]=true
 return true,nil
}
func (s *tenantScopedTestStore) ClaimEvent(d Delivery) (bool,error) {
 s.claims++
 return s.Claim(d.EventID)
}

func TestTLSIngressRejectsCrossTenantEventsBeforeStorage(t *testing.T) {
 key := []byte("12345678901234567890123456789012")
 stamp := time.Unix(1700000000, 0)
 store := &tenantScopedTestStore{company:"tenant-a",seen:map[string]bool{}}
 server := httptest.NewTLSServer(Ingress{Key:key,Store:store,Clock:func()time.Time{return stamp}})
 defer server.Close()
 client := server.Client()
 client.Timeout=3*time.Second
 deliver := func(body []byte) int {
  t.Helper()
  mac:=hmac.New(sha256.New,key)
  mac.Write([]byte(strconv.FormatInt(stamp.Unix(),10)+"."));mac.Write(body)
  req,err:=http.NewRequest(http.MethodPost,server.URL+"/internal/events",bytes.NewReader(body))
  if err!=nil {t.Fatal(err)}
  req.Header.Set("Content-Type","application/json")
  req.Header.Set("X-CB-Timestamp",strconv.FormatInt(stamp.Unix(),10))
  req.Header.Set("X-CB-Signature",hex.EncodeToString(mac.Sum(nil)))
  resp,err:=client.Do(req)
  if err!=nil {t.Fatal(err)}
  defer resp.Body.Close()
  return resp.StatusCode
 }
 foreign:=[]byte(`{"aggregate_id":"record-1","company_id":"tenant-b","event_id":"event-1","event_type":"invoice.issued","version":1}`)
 if got:=deliver(foreign);got!=http.StatusForbidden {t.Fatalf("foreign tenant: got %d, want 403",got)}
 if store.claims!=0 {t.Fatalf("cross-tenant event reached storage %d times",store.claims)}
 local:=[]byte(`{"aggregate_id":"record-1","company_id":"tenant-a","event_id":"event-1","event_type":"invoice.issued","version":1}`)
 if got:=deliver(local);got!=http.StatusAccepted {t.Fatalf("allowed tenant: got %d, want 202",got)}
 if got:=deliver(local);got!=http.StatusOK {t.Fatalf("duplicate: got %d, want 200",got)}
 if store.claims!=2 {t.Fatalf("expected two authorized storage calls, got %d",store.claims)}
}
