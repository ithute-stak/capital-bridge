package main

import (
 "encoding/json"
 "io"
 "net/http"
 "strconv"
 "time"
)

// ReplayStore must atomically persist a unique event ID before acknowledgement.
// A deployment implementation MUST be shared across Go replicas (e.g. PostgreSQL).
type ReplayStore interface { Claim(eventID string) (bool,error) }

type Ingress struct { Key []byte; Store ReplayStore; Clock func()time.Time }

func (i Ingress) ServeHTTP(w http.ResponseWriter,r *http.Request) {
 if r.Method!=http.MethodPost {http.Error(w,"method not allowed",405);return}
 if i.Store==nil || i.Clock==nil || len(i.Key)<32 {http.Error(w,"service unavailable",503);return}
 if r.Header.Get("Content-Type")!="application/json" {http.Error(w,"JSON required",415);return}
 if r.ContentLength>65536 {http.Error(w,"payload too large",413);return}
 ts,err:=strconv.ParseInt(r.Header.Get("X-CB-Timestamp"),10,64)
 if err!=nil || abs(i.Clock().Unix()-ts)>120 {http.Error(w,"stale delivery",401);return}
 body,readErr:=io.ReadAll(io.LimitReader(r.Body,65537))
 if readErr!=nil {http.Error(w,"read error",400);return}
 if len(body)>65536 {http.Error(w,"payload too large",413);return}
 // Timestamp is bound to the signed body to stop header substitution.
 if VerifyDeliveryMAC(i.Key,append([]byte(strconv.FormatInt(ts,10)+"."),body...),r.Header.Get("X-CB-Signature"))!=nil {
  http.Error(w,"unauthorised",401);return
 }
 var event Delivery
 if json.Unmarshal(body,&event)!=nil || validateDelivery(event)!=nil {http.Error(w,"invalid event",400);return}
 if scoped,ok:=i.Store.(interface{ AllowedCompany() string });ok && scoped.AllowedCompany()!=event.CompanyID {http.Error(w,"company mismatch",403);return}
 var accepted bool
 if atomic,ok:=i.Store.(interface{ClaimEvent(Delivery)(bool,error)});ok {
  accepted,err=atomic.ClaimEvent(event)
 } else {
  // Legacy stores cannot promise atomic notification persistence.
  http.Error(w,"atomic notification store required",503);return
 }
 if err!=nil {http.Error(w,"durable replay store unavailable",503);return}
 if !accepted {w.WriteHeader(http.StatusOK);return} // idempotent duplicate acknowledgement
 w.WriteHeader(http.StatusAccepted)
}
func abs(v int64)int64 {if v<0{return -v};return v}
