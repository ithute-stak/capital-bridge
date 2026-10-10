package main

import (
 "context"
 "database/sql"
 "errors"
)

// PostgresJournalReplay reads a bounded page of committed notifications after
// a company-scoped cursor. Call only after authenticating and authorizing the
// subscriber; the database role must also enforce tenant access.
type PostgresJournalReplay struct { DB *sql.DB }

func (r PostgresJournalReplay) ReplayAfter(ctx context.Context, companyID, cursorID string, limit int) ([]JournalNotification, error) {
 if r.DB == nil || !signalUUID.MatchString(companyID) || !signalUUID.MatchString(cursorID) || limit < 1 || limit > 100 {
  return nil, errors.New("invalid journal replay request")
 }
 // Reject foreign or unknown cursors rather than silently skipping history.
 var cursorFound bool
 if err := r.DB.QueryRowContext(ctx,
  "SELECT EXISTS(SELECT 1 FROM cb.realtime_notifications WHERE company_id=$1::uuid AND id=$2::uuid)",
  companyID,cursorID).Scan(&cursorFound); err != nil { return nil, err }
 if !cursorFound { return nil, sql.ErrNoRows }
 rows, err := r.DB.QueryContext(ctx, `
  SELECT n.id::text, n.company_id::text, n.event_type, n.aggregate_id::text
  FROM cb.realtime_notifications n
  JOIN cb.realtime_notifications cursor
    ON cursor.company_id=$1::uuid AND cursor.id=$2::uuid
  WHERE n.company_id=$1::uuid
    AND (n.received_at,n.id) > (cursor.received_at,cursor.id)
  ORDER BY n.received_at,n.id
  LIMIT $3`,companyID,cursorID,limit)
 if err != nil { return nil,err }
 defer rows.Close()
 events:=make([]JournalNotification,0)
 for rows.Next() {
  var n JournalNotification
  if err:=rows.Scan(&n.EventID,&n.CompanyID,&n.EventType,&n.AggregateID); err!=nil{return nil,err}
  if n.CompanyID!=companyID{return nil,errors.New("replay tenant mismatch")}
  events=append(events,n)
 }
 return events,rows.Err()
}
