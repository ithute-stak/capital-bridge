//go:build postgres_integration

package main

import (
 "bytes"
 "crypto/hmac"
 "crypto/sha256"
 "database/sql"
 "encoding/hex"
 "net/http"
 "net/http/httptest"
 "os"
 "strconv"
 "testing"
 "time"

 _ "github.com/lib/pq"
)

// TestTLSIngressPersistsSignedEvent verifies transport + authenticated ingress
// + PostgreSQL persistence through a real TLS listener, not an in-memory recorder.
func TestTLSIngressPersistsSignedEvent(t *testing.T) {
 dsn := os.Getenv("CB_TEST_POSTGRES_URL")
 if dsn == "" { t.Skip("CB_TEST_POSTGRES_URL not supplied") }
 db, err := sql.Open("postgres", dsn)
 if err != nil { t.Fatal(err) }
 company := "f1111111-1111-4111-8111-111111111111"
 eventID := "f2222222-2222-4222-8222-222222222222"
 t.Cleanup(func() {
  db.Exec("DELETE FROM cb.realtime_notifications WHERE id=$1", eventID)
  db.Exec("DELETE FROM cb.finance_event_receipts WHERE event_id=$1", eventID)
  db.Exec("DELETE FROM cb.companies WHERE id=$1", company)
  db.Close()
 })
 if _, err := db.Exec("INSERT INTO cb.companies(id, legal_name) VALUES($1, 'TLS ingress integration')", company); err != nil { t.Fatal(err) }
 key := []byte("12345678901234567890123456789012")
 stamp := time.Unix(1700000000, 0)
 handler := Ingress{Key: key, Store: AtomicNotificationStore{DB: db, CompanyID: company}, Clock: func() time.Time { return stamp }}
 server := httptest.NewTLSServer(handler)
 defer server.Close()
 client := server.Client()
 client.Timeout = 3 * time.Second
 body := []byte(`{"aggregate_id":"f3333333-3333-4333-8333-333333333333","company_id":"f1111111-1111-4111-8111-111111111111","event_id":"f2222222-2222-4222-8222-222222222222","event_type":"client.updated","version":1}`)
 mac := hmac.New(sha256.New, key)
 mac.Write([]byte(strconv.FormatInt(stamp.Unix(),10) + "."))
 mac.Write(body)
 signature := hex.EncodeToString(mac.Sum(nil))
 send := func(sig string) int {
  t.Helper()
  req, err := http.NewRequest(http.MethodPost, server.URL+"/internal/events", bytes.NewReader(body))
  if err != nil { t.Fatal(err) }
  req.Header.Set("Content-Type", "application/json")
  req.Header.Set("X-CB-Timestamp", strconv.FormatInt(stamp.Unix(),10))
  req.Header.Set("X-CB-Signature", sig)
  resp, err := client.Do(req)
  if err != nil { t.Fatal(err) }
  defer resp.Body.Close()
  return resp.StatusCode
 }
 if got := send("invalid"); got != http.StatusUnauthorized { t.Fatalf("invalid signature: %d", got) }
 if got := send(signature); got != http.StatusAccepted { t.Fatalf("first accepted event: %d", got) }
 if got := send(signature); got != http.StatusOK { t.Fatalf("duplicate event: %d", got) }
 var receipts, notifications int
 if err := db.QueryRow("SELECT COUNT(*) FROM cb.finance_event_receipts WHERE event_id=$1",eventID).Scan(&receipts); err != nil { t.Fatal(err) }
 if err := db.QueryRow("SELECT COUNT(*) FROM cb.realtime_notifications WHERE id=$1",eventID).Scan(&notifications); err != nil { t.Fatal(err) }
 if receipts != 1 || notifications != 1 { t.Fatalf("receipts=%d notifications=%d; want 1 each",receipts,notifications) }
}
