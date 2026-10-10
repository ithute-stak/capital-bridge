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
 "strconv"
 "testing"
 "os"
 "time"
 _ "github.com/lib/pq"
)
func TestSignedIngressCommitsNotificationToPostgres(t *testing.T) {
 dsn:=os.Getenv("CB_TEST_POSTGRES_URL")
 if dsn=="" {t.Skip("CB_TEST_POSTGRES_URL not supplied")}
 db,err:=sql.Open("postgres",dsn);if err!=nil{t.Fatal(err)}
 defer db.Close()
 company:="d1111111-1111-4111-8111-111111111111"
 if _,err=db.Exec("INSERT INTO cb.companies(id,legal_name) VALUES($1,'Ingress test') ON CONFLICT(id) DO NOTHING",company);err!=nil{t.Fatal(err)}
 defer db.Exec("DELETE FROM cb.companies WHERE id=$1",company)
 event:="d2222222-2222-4222-8222-222222222222"
 key:=[]byte("12345678901234567890123456789012")
 ts:=time.Unix(1700000000,0)
 h:=Ingress{Key:key,Store:AtomicNotificationStore{DB:db,CompanyID:company},Clock:func()time.Time{return ts}}
 body:=[]byte(`{"aggregate_id":"d3333333-3333-4333-8333-333333333333","company_id":"d1111111-1111-4111-8111-111111111111","event_id":"d2222222-2222-4222-8222-222222222222","event_type":"client.updated","version":1}`)
 mac:=hmac.New(sha256.New,key);mac.Write([]byte("1700000000."));mac.Write(body)
 signature:=hex.EncodeToString(mac.Sum(nil))
 send:=func()int {
  req:=httptest.NewRequest(http.MethodPost,"/internal/events",bytes.NewReader(body))
  req.Header.Set("Content-Type","application/json")
  req.Header.Set("X-CB-Timestamp",strconv.FormatInt(ts.Unix(),10))
  req.Header.Set("X-CB-Signature",signature)
  w:=httptest.NewRecorder();h.ServeHTTP(w,req);return w.Code
 }
 if got:=send();got!=202{t.Fatalf("first delivery: %d",got)}
 if got:=send();got!=200{t.Fatalf("duplicate: %d",got)}
 var receipts,notices int
 if err=db.QueryRow("SELECT COUNT(*) FROM cb.finance_event_receipts WHERE event_id=$1",event).Scan(&receipts);err!=nil{t.Fatal(err)}
 if err=db.QueryRow("SELECT COUNT(*) FROM cb.realtime_notifications WHERE id=$1",event).Scan(&notices);err!=nil{t.Fatal(err)}
 if receipts!=1 || notices!=1 {t.Fatalf("receipt=%d notification=%d",receipts,notices)}
 defer db.Exec("DELETE FROM cb.realtime_notifications WHERE id=$1",event)
 defer db.Exec("DELETE FROM cb.finance_event_receipts WHERE event_id=$1",event)
}
