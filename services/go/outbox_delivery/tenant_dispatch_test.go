package main

import (
 "context"
 "errors"
 "testing"
)
type resolverStub struct { value JournalNotification; err error }
func (s resolverStub) ResolveNotification(context.Context,CommitSignal)(JournalNotification,error){return s.value,s.err}
type publisherStub struct { calls int; company string }
func (s *publisherStub) PublishTenant(_ context.Context,company string,_ JournalNotification)error{s.calls++;s.company=company;return nil}
func TestDispatchCommitSignalTenantIsolation(t *testing.T){
 ctx:=context.Background()
 hint:=CommitSignal{CompanyID:"11111111-1111-4111-8111-111111111111",EventID:"22222222-2222-4222-8222-222222222222"}
 valid:=JournalNotification{CompanyID:hint.CompanyID,EventID:hint.EventID,EventType:"client.updated",AggregateID:"33333333-3333-4333-8333-333333333333"}
 pub:=&publisherStub{}
 if err:=DispatchCommitSignal(ctx,hint,resolverStub{value:valid},pub);err!=nil{t.Fatal(err)}
 if pub.calls!=1 || pub.company!=hint.CompanyID{t.Fatal("expected exactly one tenant-scoped publish")}
 pub.calls=0
 foreign:=valid;foreign.CompanyID="44444444-4444-4444-8444-444444444444"
 if err:=DispatchCommitSignal(ctx,hint,resolverStub{value:foreign},pub);err==nil{t.Fatal("accepted foreign company row")}
 if pub.calls!=0{t.Fatal("cross-tenant publication occurred")}
 if err:=DispatchCommitSignal(ctx,hint,resolverStub{err:errors.New("journal unavailable")},pub);err==nil{t.Fatal("ignored journal failure")}
 if pub.calls!=0{t.Fatal("publication after journal failure")}
}
