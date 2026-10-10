package main

import (
 "context"
 "testing"
)

func TestListenCommitSignalsRejectsInvalidConfiguration(t *testing.T) {
 handler := func(context.Context, CommitSignal) error { return nil }
 if err := ListenCommitSignals(context.Background(), "", handler); err == nil {
  t.Fatal("empty DSN must fail closed")
 }
 if err := ListenCommitSignals(context.Background(), "not-used", nil); err == nil {
  t.Fatal("nil handler must fail closed")
 }
}
