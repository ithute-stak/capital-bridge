package main

import (
 "context"
 "errors"
)

// RunLiveTenantNotifications bridges PostgreSQL commit hints to the durable
// journal resolver and the tenant-isolated hub. It never publishes raw NOTIFY
// payloads; callers supply a database identity with appropriate journal access.
// A production supervisor must restart and reconcile after listener failures.
func RunLiveTenantNotifications(ctx context.Context, dsn string, resolver NotificationResolver, hub *TenantHub) error {
 return runLiveTenantNotificationsReady(ctx,dsn,resolver,hub,nil)
}

func runLiveTenantNotificationsReady(ctx context.Context,dsn string,resolver NotificationResolver,hub *TenantHub,ready func())error {
 if dsn=="" || resolver==nil || hub==nil{return errors.New("live notifications not configured")}
 return listenCommitSignalsReady(ctx,dsn,func(ctx context.Context,hint CommitSignal) error {
  return DispatchCommitSignal(ctx,hint,resolver,hub)
 },ready)
}
