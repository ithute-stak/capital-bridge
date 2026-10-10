package main
import (
 "net/http"
 "net/http/httptest"
 "testing"
)
func TestHealthWithoutDatabaseFailsClosed(t *testing.T){
 w:=httptest.NewRecorder()
 HealthHandler(nil).ServeHTTP(w,httptest.NewRequest(http.MethodGet,"/internal/health",nil))
 if w.Code!=http.StatusServiceUnavailable {t.Fatalf("unexpected health code %d",w.Code)}
 if w.Body.String()=="" {t.Fatal("missing bounded failure response")}
}
func TestHealthRejectsUnsupportedMethods(t *testing.T){
 w:=httptest.NewRecorder()
 HealthHandler(nil).ServeHTTP(w,httptest.NewRequest(http.MethodPost,"/internal/health",nil))
 if w.Code!=http.StatusMethodNotAllowed {t.Fatalf("unexpected health code %d",w.Code)}
}
