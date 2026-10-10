package main

import (
 "encoding/json"
 "fmt"
 "net/http"
 "net/url"
 "strings"
 "time"
)

// SessionFromRequest is implemented by trusted server-side middleware.
// Do not accept session tokens in query parameters or client company headers.
type SessionFromRequest func(*http.Request) (string, error)

// SSESubscription exposes a bounded server-sent event stream only after
// session verification and company authorization. Browser integration must
// also apply same-origin cookie protections and deployment TLS.
type SSESubscription struct {
 Hub *TenantHub
 Verifier SessionSubscriptionVerifier
 Authorizer CompanySubscriptionAuthorizer
 Session SessionFromRequest
 AllowedOrigin string
 RevalidateInterval time.Duration
}

func (s SSESubscription) ServeHTTP(w http.ResponseWriter,r *http.Request) {
 if r.Method!=http.MethodGet {http.Error(w,"method not allowed",http.StatusMethodNotAllowed);return}
 if s.Hub==nil || s.Verifier==nil || s.Authorizer==nil || s.Session==nil {
  http.Error(w,"service unavailable",http.StatusServiceUnavailable);return
 }
 if s.AllowedOrigin=="" || !validSSEOrigin(r,s.AllowedOrigin) {http.Error(w,"origin forbidden",http.StatusForbidden);return}
 flusher,ok:=w.(http.Flusher);if !ok {http.Error(w,"stream unavailable",http.StatusInternalServerError);return}
 if _,err:=ParseReplayCursor(r);err!=nil {http.Error(w,"invalid replay cursor",http.StatusBadRequest);return}
 token,err:=s.Session(r)
 if err!=nil || token=="" {http.Error(w,"unauthorized",http.StatusUnauthorized);return}
 initial,err:=s.Verifier.VerifySubscriptionSession(r.Context(),token)
 if err!=nil || initial.Subject=="" || !signalUUID.MatchString(initial.CompanyID) {http.Error(w,"forbidden",http.StatusForbidden);return}
 ch:=make(chan JournalNotification,32)
 stop,err:=AdmitSessionSubscription(r.Context(),s.Hub,s.Verifier,s.Authorizer,token,ch)
 if err!=nil {http.Error(w,"forbidden",http.StatusForbidden);return}
 defer stop()
 w.Header().Set("Content-Type","text/event-stream")
 w.Header().Set("Cache-Control","no-store")
 w.Header().Set("X-Content-Type-Options","nosniff")
 w.WriteHeader(http.StatusOK)
 flusher.Flush()
 interval:=s.RevalidateInterval
 if interval<=0 || interval>time.Minute {interval=30*time.Second}
 revalidate:=time.NewTicker(interval)
 defer revalidate.Stop()
 heartbeat:=time.NewTicker(20*time.Second)
 defer heartbeat.Stop()
 for {
  select {
  case <-r.Context().Done():return
  case <-revalidate.C:
   principal,err:=s.Verifier.VerifySubscriptionSession(r.Context(),token)
   if err!=nil || principal.Subject!=initial.Subject || principal.CompanyID!=initial.CompanyID {return}
   if err=s.Authorizer.AuthorizeSubscription(r.Context(),principal);err!=nil{return}
  case n:=<-ch:
   data,err:=json.Marshal(n);if err!=nil{return}
   if _,err=fmt.Fprintf(w,"event: notification\ndata: %s\n\n",data);err!=nil{return}
   flusher.Flush()
  case <-heartbeat.C:
   if _,err:=fmt.Fprint(w,": heartbeat\n\n");err!=nil{return}
   flusher.Flush()
  }
 }
}

// Require a configured HTTPS origin and reject cross-site browser attempts.
// Requests without Origin are rejected, including non-browser clients.
func validSSEOrigin(r *http.Request, allowed string) bool {
 expected,err:=url.Parse(allowed)
 if err!=nil || expected.Scheme!="https" || expected.Host=="" || expected.User!=nil || expected.Path!="" || expected.RawQuery!="" || expected.Fragment!="" {return false}
 raw:=r.Header.Get("Origin")
 if raw=="" || strings.Contains(raw,",") {return false}
 actual,err:=url.Parse(raw)
 if err!=nil || actual.Scheme!="https" || actual.Host=="" || actual.User!=nil || actual.Path!="" || actual.RawQuery!="" || actual.Fragment!="" {return false}
 return strings.EqualFold(expected.Scheme,actual.Scheme) && strings.EqualFold(expected.Host,actual.Host)
}
