package main

import (
    "context"
    "database/sql"
    "errors"
    "regexp"
)

var uuidPattern = regexp.MustCompile(`^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$`)

// SQLReplayStore stores durable event IDs using an atomic PostgreSQL insert.
// A deployment must configure a dedicated, least-privilege company-scoped DB role.
type SQLReplayStore struct {
    DB *sql.DB
    CompanyID string
}

func (s SQLReplayStore) AllowedCompany() string {
    return s.CompanyID
}

func (s SQLReplayStore) Claim(eventID string) (bool, error) {
    if s.DB == nil {
        return false, errors.New("replay database unavailable")
    }
    if !uuidPattern.MatchString(eventID) || !uuidPattern.MatchString(s.CompanyID) {
        return false, errors.New("invalid replay identity")
    }
    tx, err := s.DB.BeginTx(context.Background(), nil)
    if err != nil { return false, err }
    defer tx.Rollback()
    if _, err = tx.ExecContext(context.Background(),
        "SELECT set_config('app.company_id',$1,true)", s.CompanyID); err != nil {
        return false, err
    }
    result, err := tx.ExecContext(context.Background(),
        `INSERT INTO cb.finance_event_receipts(event_id,company_id)
         VALUES($1,$2) ON CONFLICT(event_id) DO NOTHING`,
        eventID, s.CompanyID)
    if err != nil {
        return false, err
    }
    count, err := result.RowsAffected()
    if err != nil { return false, err }
    if err = tx.Commit(); err != nil { return false, err }
    return count == 1, nil
}
