package main

import (
 "context"
 "database/sql"
 "net/http"
 "time"
)

// HealthHandler reports availability only when a bounded database ping succeeds.
// This endpoint discloses no database connection details or credentials.
func HealthHandler(db *sql.DB) http.Handler {
 return http.HandlerFunc(func(w http.ResponseWriter,r *http.Request){
  if r.Method!=http.MethodGet {w.WriteHeader(http.StatusMethodNotAllowed);return}
  if db==nil {http.Error(w,"unavailable",http.StatusServiceUnavailable);return}
  ctx,cancel:=context.WithTimeout(r.Context(),2*time.Second)
  defer cancel()
  if err:=db.PingContext(ctx);err!=nil {http.Error(w,"unavailable",http.StatusServiceUnavailable);return}
  w.Header().Set("Cache-Control","no-store")
  w.WriteHeader(http.StatusOK)
  _,_=w.Write([]byte("ok"))
 })
}
