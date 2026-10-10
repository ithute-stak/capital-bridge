package main

import (
 "errors"
 "net/http"
 "strings"
)

// ReplayCursor is an opaque event ID supplied by EventSource on reconnect.
// It is only a position hint: every replay query must independently verify
// the authenticated company and enforce its row-level permissions.
type ReplayCursor struct { EventID string }

// ParseReplayCursor rejects unsupported/malformed Last-Event-ID values.
// An absent cursor indicates a fresh stream, not an authorization decision.
func ParseReplayCursor(r *http.Request) (ReplayCursor,error) {
 if r==nil {return ReplayCursor{},errors.New("missing request")}
 raw:=r.Header.Get("Last-Event-ID")
 if raw=="" {return ReplayCursor{},nil}
 if len(raw)>64 || strings.TrimSpace(raw)!=raw || !signalUUID.MatchString(raw) {
  return ReplayCursor{},errors.New("invalid replay cursor")
 }
 return ReplayCursor{EventID:raw},nil
}
