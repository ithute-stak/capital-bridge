package main

import (
 "encoding/json"
 "fmt"
 "os"
)
// Envelope defines a versioned event payload; this prototype never publishes data.
type Envelope struct {
 Version int `json:"version"`
 CompanyID string `json:"company_id"`
 EventType string `json:"event_type"`
 AggregateID string `json:"aggregate_id"`
}
func valid(e Envelope) bool {
 return e.Version == 1 && e.CompanyID != "" && e.EventType != "" && e.AggregateID != ""
}
func main() {
 var e Envelope
 if err := json.NewDecoder(os.Stdin).Decode(&e); err != nil || !valid(e) {
  fmt.Fprintln(os.Stderr,"invalid event envelope"); os.Exit(2)
 }
 if err := json.NewEncoder(os.Stdout).Encode(e); err != nil { os.Exit(2) }
}
