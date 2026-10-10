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

// TestIngressRetriesAfterPostgresConstraintFailure proves that a failed
// receipt/notification transaction is not acknowledged or remembered, and
// that retrying the same signed payload can commit once its dependency exists.
func TestIngressRetriesAfterPostgresConstraintFailure(t *testing.T) {
    dsn := os.Getenv("CB_TEST_POSTGRES_URL")
    if dsn == "" {
        t.Skip("CB_TEST_POSTGRES_URL not supplied")
    }
    db, err := sql.Open("postgres", dsn)
    if err != nil { t.Fatal(err) }
    t.Cleanup(func() { if err := db.Close(); err != nil { t.Error(err) } })

    company := "e1111111-1111-4111-8111-111111111111"
    event := "e2222222-2222-4222-8222-222222222222"
    // Cleanup must run even when an assertion fails.
    t.Cleanup(func() {
        // Remove dependent rows before their owning company.
        if _, err := db.Exec("DELETE FROM cb.realtime_notifications WHERE id=$1", event); err != nil { t.Error(err) }
        if _, err := db.Exec("DELETE FROM cb.finance_event_receipts WHERE event_id=$1", event); err != nil { t.Error(err) }
        if _, err := db.Exec("DELETE FROM cb.companies WHERE id=$1", company); err != nil { t.Error(err) }
    })

    // Start with a missing referenced company; ensure an earlier run left
    // no fixture behind (this test uses reserved deterministic IDs).
    if _, err := db.Exec("DELETE FROM cb.realtime_notifications WHERE id=$1", event); err != nil { t.Fatal(err) }
    if _, err := db.Exec("DELETE FROM cb.finance_event_receipts WHERE event_id=$1", event); err != nil { t.Fatal(err) }
    if _, err := db.Exec("DELETE FROM cb.companies WHERE id=$1", company); err != nil { t.Fatal(err) }

    key := []byte("12345678901234567890123456789012")
    stamp := time.Unix(1700000000, 0)
    handler := Ingress{Key: key, Store: AtomicNotificationStore{DB: db, CompanyID: company}, Clock: func() time.Time { return stamp }}
    body := []byte(`{"aggregate_id":"e3333333-3333-4333-8333-333333333333","company_id":"e1111111-1111-4111-8111-111111111111","event_id":"e2222222-2222-4222-8222-222222222222","event_type":"client.updated","version":1}`)
    mac := hmac.New(sha256.New, key)
    mac.Write([]byte(strconv.FormatInt(stamp.Unix(), 10) + "."))
    mac.Write(body)
    signature := hex.EncodeToString(mac.Sum(nil))

    send := func() int {
        req := httptest.NewRequest(http.MethodPost, "/internal/events", bytes.NewReader(body))
        req.Header.Set("Content-Type", "application/json")
        req.Header.Set("X-CB-Timestamp", strconv.FormatInt(stamp.Unix(), 10))
        req.Header.Set("X-CB-Signature", signature)
        w := httptest.NewRecorder()
        handler.ServeHTTP(w, req)
        return w.Code
    }
    assertCounts := func(want int) {
        t.Helper()
        var receipts, notifications int
        if err := db.QueryRow("SELECT COUNT(*) FROM cb.finance_event_receipts WHERE event_id=$1", event).Scan(&receipts); err != nil { t.Fatal(err) }
        if err := db.QueryRow("SELECT COUNT(*) FROM cb.realtime_notifications WHERE id=$1", event).Scan(&notifications); err != nil { t.Fatal(err) }
        if receipts != want || notifications != want {
            t.Fatalf("receipt=%d notification=%d; want %d each", receipts, notifications, want)
        }
    }

    if got := send(); got != http.StatusServiceUnavailable { t.Fatalf("missing-company delivery: got %d, want 503", got) }
    assertCounts(0)
    if _, err := db.Exec("INSERT INTO cb.companies(id,legal_name) VALUES($1,'Recovery ingress test')", company); err != nil { t.Fatal(err) }
    if got := send(); got != http.StatusAccepted { t.Fatalf("retry delivery: got %d, want 202", got) }
    if got := send(); got != http.StatusOK { t.Fatalf("duplicate delivery: got %d, want 200", got) }
    assertCounts(1)
}
