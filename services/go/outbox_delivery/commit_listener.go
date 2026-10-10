package main

import (
 "context"
 "errors"
 "time"

 "github.com/lib/pq"
)

const realtimeChannel = "cb_realtime_events"

// ListenCommitSignals subscribes to committed PostgreSQL notification hints.
// Notifications are untrusted hints, not authorization or guaranteed delivery.
// Consumers must retrieve rows with authenticated tenant context and replay
// missed events from the durable journal after reconnects.
func ListenCommitSignals(ctx context.Context, dsn string, handle func(context.Context, CommitSignal) error) error {
 return listenCommitSignalsReady(ctx,dsn,handle,nil)
}

func listenCommitSignalsReady(ctx context.Context, dsn string, handle func(context.Context, CommitSignal) error, ready func()) error {
 if dsn == "" || handle == nil { return errors.New("listener requires a DSN and callback") }
 listener := pq.NewListener(dsn, 2*time.Second, 30*time.Second, nil)
 if err := listener.Listen(realtimeChannel); err != nil { listener.Close(); return err }
 defer listener.Close()
 if ready!=nil {ready()}
 for {
  select {
  case <-ctx.Done():
   return ctx.Err()
  case n, ok := <-listener.Notify:
   if !ok { return errors.New("notification channel closed") }
   if n == nil {
    // lib/pq signals reconnection with nil; caller must reconcile journal
    // independently, since NOTIFY is not a durable event stream.
    continue
   }
   signal, err := ParseCommitSignal(n.Extra)
   if err != nil { continue }
   if err := handle(ctx, signal); err != nil { return err }
  }
 }
}
