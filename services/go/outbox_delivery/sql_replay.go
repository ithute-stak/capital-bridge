package main

import (
 "context"
 "database/sql"
 "errors"
 "github.com/google/uuid"
)

// SQLReplayStore uses an atomic INSERT ON CONFLICT to reject replays across
// restarts and replicas. Inject a database connection with least privileges.
// The Go internal service must use a dedicated DB role and a reviewed RLS policy.
type SQLReplayStore struct { DB *sql.DB; CompanyID string }

func (s SQLReplayStore) Claim(eventID string) (bool,error) {
 if s.DB==nil {return false,errors.New("replay database unavailable")}
 event,err:=uuid.Parse(eventID)
 if err!=nil{return false,errors.New("invalid event identifier")}
 company,err:=uuid.Parse(s.CompanyID)
 if err!=nil{return false,errors.New("invalid company identifier")}
 result,err:=s.DB.ExecContext(context.Background(),
   `INSERT INTO cb.finance_event_receipts(event_id,company_id)
     VALUES($1,$2) ON CONFLICT(event_id) DO NOTHING`,event,company)
 if err!=nil{return false,err}
 count,err:=result.RowsAffected()
 return count==1,err
}
