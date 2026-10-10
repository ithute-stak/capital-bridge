package main

import (
 "encoding/json"
 "context"
 "fmt"
 "net/http"
 "net/url"
 "strings"
 "time"
)

// SessionFromRequest is implemented by trusted server-side middleware.
// Do not accept session tokens in query parameters or client company headers.
type SessionFromRequest func(*http.Request) (string, error)

type JournalReplayReader interface {
 ReplayAfter(context.Context,string,string,int)([]JournalNotification,error)
}

// SSESubscription exposes a bounded server-sent event stream only after
// session verification and company authorization. Browser integration must
// also apply same-origin cookie protections and deployment TLS.
type SSESubscription struct {
 Hub *TenantHub
 Replay JournalReplayReader
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
 cursor,err:=ParseReplayCursor(r)
 if err!=nil {http.Error(w,"invalid replay cursor",http.StatusBadRequest);return}
 token,err:=s.Session(r)
 if err!=nil || token=="" {http.Error(w,"unauthorized",http.StatusUnauthorized);return}
 initial,err:=s.Verifier.VerifySubscriptionSession(r.Context(),token)
 if err!=nil || initial.Subject=="" || !signalUUID.MatchString(initial.CompanyID) {http.Error(w,"forbidden",http.StatusForbidden);return}
 ch:=make(chan JournalNotification,32)
 stop,err:=AdmitSessionSubscription(r.Context(),s.Hub,s.Verifier,s.Authorizer,token,ch)
 if err!=nil {http.Error(w,"forbidden",http.StatusForbidden);return}
 defer stop()
 // Subscribe before replay to avoid missing events committed during the query.
 // The bounded replay page rejects potential gaps rather than sending incomplete history.
 var backlog []JournalNotification
 if cursor.EventID!="" {
  if s.Replay==nil {http.Error(w,"replay unavailable",http.StatusServiceUnavailable);return}
  backlog,err=s.Replay.ReplayAfter(r.Context(),initial.CompanyID,cursor.EventID,100)
  if err!=nil {http.Error(w,"replay failed",http.StatusConflict);return}
  if len(backlog)==100 {http.Error(w,"replay limit exceeded",http.StatusConflict);return}
 }
 w.Header().Set("Content-Type","text/event-stream")
 w.Header().Set("Cache-Control","no-store")
 w.Header().Set("X-Content-Type-Options","nosniff")
 w.WriteHeader(http.StatusOK)
 flusher.Flush()
 // Replayed records carry SSE IDs, allowing EventSource to resume from the
 // last successfully delivered event. Duplicate live deliveries are suppressed.
 seen:=map[string]struct{}{}
 seen[cursor.EventID]=struct{}{}
 for _,n:=range backlog {
  if n.CompanyID!=initial.CompanyID {return}
  if err:=writeSSEJournal(w,flusher,n);err!=nil{return}
  seen[n.EventID]=struct{}{}
 }
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
   if n.CompanyID!=initial.CompanyID {return}
   if _,already:=seen[n.EventID];already {continue}
   if err:=writeSSEJournal(w,flusher,n);err!=nil{return}
   seen[n.EventID]=struct{}{}
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

func writeSSEJournal(w http.ResponseWriter,flusher http.Flusher,n JournalNotification)error {
 if !signalUUID.MatchString(n.EventID)||!signalUUID.MatchString(n.CompanyID){return fmt.Errorf("invalid journal notification")}
 data,err:=json.Marshal(n);if err!=nil{return err}
 if _,err=fmt.Fprintf(w,"id: %s\nevent: notification\ndata: %s\n\n",n.EventID,data);err!=nil{return err}
 flusher.Flush()
 return nil
}
