package main

import (
 "errors"
 "net/http"
 "net/http/httptest"
 "testing"
)

func TestSSESubscriptionFailsClosed(t *testing.T) {
 s:=SSESubscription{}
 w:=httptest.NewRecorder()
 s.ServeHTTP(w,httptest.NewRequest(http.MethodGet,"/events",nil))
 if w.Code!=http.StatusServiceUnavailable {t.Fatalf("unconfigured stream: %d",w.Code)}
 w=httptest.NewRecorder()
 s.ServeHTTP(w,httptest.NewRequest(http.MethodPost,"/events",nil))
 if w.Code!=http.StatusMethodNotAllowed {t.Fatalf("unexpected method status: %d",w.Code)}
 s=SSESubscription{Hub:NewTenantHub(),Verifier:&sessionVerifierStub{},Authorizer:&admissionAuthStub{},Session:func(*http.Request)(string,error){return "",errors.New("no session")},AllowedOrigin:"https://capitalbridge.co.ls"}
 w=httptest.NewRecorder()
 req:=httptest.NewRequest(http.MethodGet,"/events",nil)
 req.Header.Set("Origin","https://capitalbridge.co.ls")
 s.ServeHTTP(w,req)
 if w.Code!=http.StatusUnauthorized {t.Fatalf("missing session: %d",w.Code)}
}
