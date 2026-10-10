package main

import (
 "encoding/json"
 "errors"
 "regexp"
 "strings"
 "io"
)

// CommitSignal is a database wake-up hint, not proof of user authorization.
// Subscribers must fetch the row under the authenticated company's scope.
type CommitSignal struct {
 CompanyID string `json:"company_id"`
 EventID string `json:"event_id"`
}

var signalUUID = regexp.MustCompile(`^[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[1-8][a-fA-F0-9]{3}-[89aAbB][a-fA-F0-9]{3}-[a-fA-F0-9]{12}$`)

// ParseCommitSignal rejects malformed NOTIFY payloads before any database lookup.
func ParseCommitSignal(payload string) (CommitSignal, error) {
 var signal CommitSignal
 if len(payload) == 0 || len(payload) > 1024 { return signal, errors.New("invalid notification payload size") }
 dec := json.NewDecoder(strings.NewReader(payload))
 dec.DisallowUnknownFields()
 if err := dec.Decode(&signal); err != nil { return CommitSignal{}, err }
 var extra any
 if err := dec.Decode(&extra); err != io.EOF { return CommitSignal{}, errors.New("trailing notification payload") }
 if !signalUUID.MatchString(signal.CompanyID) || !signalUUID.MatchString(signal.EventID) {
  return CommitSignal{}, errors.New("invalid notification identifiers")
 }
 return signal, nil
}
