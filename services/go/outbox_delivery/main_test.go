package main

import "testing"

func TestValidDelivery(t *testing.T) {
 d:=Delivery{Version:1,EventID:"evt-1",CompanyID:"tenant-a",EventType:"payment.allocated",AggregateID:"allocation-1"}
 if err:=validateDelivery(d);err!=nil {t.Fatal(err)}
}
func TestRejectInvalidDelivery(t *testing.T) {
 base:=Delivery{Version:1,EventID:"evt-1",CompanyID:"tenant-a",EventType:"payment.allocated",AggregateID:"allocation-1"}
 variants:=[]Delivery{
  {Version:2,EventID:base.EventID,CompanyID:base.CompanyID,EventType:base.EventType,AggregateID:base.AggregateID},
  {Version:1,EventID:base.EventID,CompanyID:base.CompanyID,EventType:"admin.grant",AggregateID:base.AggregateID},
  {Version:1,EventID:"",CompanyID:base.CompanyID,EventType:base.EventType,AggregateID:base.AggregateID},
  {Version:1,EventID:base.EventID,CompanyID:"  ",EventType:base.EventType,AggregateID:base.AggregateID},
 }
 for _,d:=range variants {if err:=validateDelivery(d);err==nil {t.Fatalf("accepted invalid delivery: %+v",d)}}
}
