package main

import (
 "context"
 "database/sql"
 "errors"
)

// PostgresJournalResolver fetches the durable notification using BOTH tenant
// and event identifiers. It is a server-side component, never a browser API.
// Browser authorization and PostgreSQL row-level access remain mandatory
// at the subscription boundary.
type PostgresJournalResolver struct {
 DB *sql.DB
}
func (r PostgresJournalResolver) ResolveNotification(ctx context.Context, hint CommitSignal) (JournalNotification,error) {
 if r.DB==nil {return JournalNotification{},errors.New("journal database not configured")}
 if !signalUUID.MatchString(hint.CompanyID)||!signalUUID.MatchString(hint.EventID) {
  return JournalNotification{},errors.New("invalid journal identity")
 }
 var n JournalNotification
 err:=r.DB.QueryRowContext(ctx,`
  SELECT id::text, company_id::text, event_type, aggregate_id::text
  FROM cb.realtime_notifications
  WHERE company_id=$1::uuid AND id=$2::uuid
 `,hint.CompanyID,hint.EventID).Scan(&n.EventID,&n.CompanyID,&n.EventType,&n.AggregateID)
 if err!=nil{return JournalNotification{},err}
 if n.CompanyID!=hint.CompanyID||n.EventID!=hint.EventID {return JournalNotification{},errors.New("journal identity mismatch")}
 return n,nil
}
