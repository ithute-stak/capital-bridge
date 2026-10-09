package main

import (
 "context"
 "database/sql"
 "errors"
)

// AtomicNotificationStore accepts replay IDs and durable notifications together.
// The caller must validate an authenticated delivery before calling ClaimEvent.
type AtomicNotificationStore struct { DB *sql.DB; CompanyID string }
func (s AtomicNotificationStore) AllowedCompany() string { return s.CompanyID }
func (s AtomicNotificationStore) Claim(eventID string)(bool,error) {
 return false,errors.New("use ClaimEvent with validated event metadata")
}
func (s AtomicNotificationStore) ClaimEvent(d Delivery)(bool,error) {
 if s.DB==nil{return false,errors.New("notification database unavailable")}
 if !uuidPattern.MatchString(d.EventID) || !uuidPattern.MatchString(d.CompanyID) ||
    !uuidPattern.MatchString(d.AggregateID) || d.CompanyID!=s.CompanyID {
  return false,errors.New("invalid event or tenant identity")
 }
 if err:=validateDelivery(d);err!=nil{return false,err}
 ctx:=context.Background()
 tx,err:=s.DB.BeginTx(ctx,nil);if err!=nil{return false,err}
 defer tx.Rollback()
 if _,err=tx.ExecContext(ctx,"SELECT set_config('app.company_id',$1,true)",d.CompanyID);err!=nil{return false,err}
 receipt,err:=tx.ExecContext(ctx,
  `INSERT INTO cb.finance_event_receipts(event_id,company_id)
    VALUES($1,$2) ON CONFLICT(event_id) DO NOTHING`,d.EventID,d.CompanyID)
 if err!=nil{return false,err}
 count,err:=receipt.RowsAffected();if err!=nil{return false,err}
 if count==0 {
  // An existing durable receipt indicates prior transaction commit.
  if err=tx.Commit();err!=nil{return false,err}
  return false,nil
 }
 if _,err=tx.ExecContext(ctx,
  `INSERT INTO cb.realtime_notifications(id,company_id,event_type,aggregate_id)
    VALUES($1,$2,$3,$4)`,d.EventID,d.CompanyID,d.EventType,d.AggregateID);err!=nil{return false,err}
 if err=tx.Commit();err!=nil{return false,err}
 return true,nil
}
