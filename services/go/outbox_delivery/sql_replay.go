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
    result, err := s.DB.ExecContext(context.Background(),
        `INSERT INTO cb.finance_event_receipts(event_id,company_id)
         VALUES($1,$2) ON CONFLICT(event_id) DO NOTHING`,
        eventID, s.CompanyID)
    if err != nil {
        return false, err
    }
    count, err := result.RowsAffected()
    return count == 1, err
}
