package main

import (
 "encoding/json"
 "fmt"
 "net/http"
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
}

func (s SSESubscription) ServeHTTP(w http.ResponseWriter,r *http.Request) {
 if r.Method!=http.MethodGet {http.Error(w,"method not allowed",http.StatusMethodNotAllowed);return}
 if s.Hub==nil || s.Verifier==nil || s.Authorizer==nil || s.Session==nil {
  http.Error(w,"service unavailable",http.StatusServiceUnavailable);return
 }
 flusher,ok:=w.(http.Flusher);if !ok {http.Error(w,"stream unavailable",http.StatusInternalServerError);return}
 token,err:=s.Session(r)
 if err!=nil || token=="" {http.Error(w,"unauthorized",http.StatusUnauthorized);return}
 ch:=make(chan JournalNotification,32)
 stop,err:=AdmitSessionSubscription(r.Context(),s.Hub,s.Verifier,s.Authorizer,token,ch)
 if err!=nil {http.Error(w,"forbidden",http.StatusForbidden);return}
 defer stop()
 w.Header().Set("Content-Type","text/event-stream")
 w.Header().Set("Cache-Control","no-store")
 w.Header().Set("X-Content-Type-Options","nosniff")
 w.WriteHeader(http.StatusOK)
 flusher.Flush()
 heartbeat:=time.NewTicker(20*time.Second)
 defer heartbeat.Stop()
 for {
  select {
  case <-r.Context().Done():return
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
