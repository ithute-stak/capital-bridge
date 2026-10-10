//go:build !capitalbridge_service

package main

import (
 "encoding/json"
 "errors"
 "strings"
 "fmt"
 "io"
 "os"
)

// Delivery is a validated, tenant-scoped finance event from a committed outbox.
// Production websocket delivery is NOT active in this prototype.
type Delivery struct {
 Version int `json:"version"`
 EventID string `json:"event_id"`
 CompanyID string `json:"company_id"`
 EventType string `json:"event_type"`
 AggregateID string `json:"aggregate_id"`
}

var allowed=map[string]bool{"invoice.issued":true,"payment.posted":true,"payment.allocated":true,"bank.matched":true,"client.created":true,"client.updated":true}

func validateDelivery(d Delivery) error {
 if d.Version!=1 || !allowed[d.EventType] {return errors.New("invalid event version or type")}
 if strings.TrimSpace(d.EventID)=="" || strings.TrimSpace(d.CompanyID)=="" || strings.TrimSpace(d.AggregateID)=="" {
  return errors.New("missing event identity")
 }
 return nil
}


func main() {
 decoder:=json.NewDecoder(io.LimitReader(os.Stdin,65536))
 decoder.DisallowUnknownFields()
 var d Delivery
 if err:=decoder.Decode(&d);err!=nil {fmt.Fprintln(os.Stderr,"invalid JSON event");os.Exit(2)}
 if err:=validateDelivery(d);err!=nil {fmt.Fprintln(os.Stderr,err);os.Exit(2)}
 var extra interface{}
 if err:=decoder.Decode(&extra);err!=io.EOF {fmt.Fprintln(os.Stderr,"multiple event objects");os.Exit(2)}
 if err:=json.NewEncoder(os.Stdout).Encode(d);err!=nil {os.Exit(2)}
}
