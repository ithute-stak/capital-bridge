package main

import (
 "context"
 "errors"
)

// JournalNotification is the immutable payload resolved from the durable journal.
// A commit signal is only a wake-up hint and MUST NOT be broadcast directly.
type JournalNotification struct {
 EventID string
 CompanyID string
 EventType string
 AggregateID string
}

type NotificationResolver interface {
 ResolveNotification(context.Context, CommitSignal) (JournalNotification, error)
}

// TenantNotificationPublisher requires an authenticated and authorized tenant
// subscription implementation; it must never use a global broadcast channel.
type TenantNotificationPublisher interface {
 PublishTenant(context.Context, string, JournalNotification) error
}

// DispatchCommitSignal resolves a hint against the journal before scoped publish.
// The resolver must enforce tenant database access and match BOTH IDs.
func DispatchCommitSignal(ctx context.Context, hint CommitSignal, resolver NotificationResolver, publisher TenantNotificationPublisher) error {
 if resolver == nil || publisher == nil { return errors.New("notification dispatch not configured") }
 if !signalUUID.MatchString(hint.CompanyID) || !signalUUID.MatchString(hint.EventID) {
  return errors.New("invalid notification hint")
 }
 notification,err:=resolver.ResolveNotification(ctx,hint)
 if err!=nil {return err}
 if notification.CompanyID!=hint.CompanyID || notification.EventID!=hint.EventID {
  return errors.New("journal notification identity mismatch")
 }
 if notification.EventType=="" || notification.AggregateID=="" {
  return errors.New("invalid journal notification")
 }
 return publisher.PublishTenant(ctx,hint.CompanyID,notification)
}
