package main

import (
 "context"
 "crypto/tls"
 "errors"
 "net"
 "testing"
 "time"
)
type nonAtomicStore struct{}
func (nonAtomicStore) Claim(string)(bool,error){return true,nil}
type atomicStub struct{}
func (atomicStub) Claim(string)(bool,error){return true,nil}
func (atomicStub) ClaimEvent(Delivery)(bool,error){return true,nil}

func TestServeIngressFailsClosedWithoutTLS(t *testing.T){
 listener,err:=net.Listen("tcp","127.0.0.1:0");if err!=nil {t.Fatal(err)}
 defer listener.Close()
 ingress:=Ingress{Key:[]byte("12345678901234567890123456789012"),Store:atomicStub{},Clock:time.Now}
 if err:=ServeIngress(context.Background(),listener,tls.Certificate{},ingress);err==nil {t.Fatal("missing TLS certificate accepted")}
}
func TestServeIngressRejectsLegacyReplayStore(t *testing.T){
 listener,err:=net.Listen("tcp","127.0.0.1:0");if err!=nil {t.Fatal(err)}
 defer listener.Close()
 ingress:=Ingress{Key:[]byte("12345678901234567890123456789012"),Store:nonAtomicStore{},Clock:time.Now}
 err=ServeIngress(context.Background(),listener,tls.Certificate{Certificate:[][]byte{{1}}},ingress)
 if err==nil {t.Fatal("legacy replay-only store accepted")}
 if !errors.Is(err,net.ErrClosed) && err.Error()!="atomic durable delivery store required" {t.Fatalf("unexpected error: %v",err)}
}
func TestServeIngressRejectsShortKey(t *testing.T){
 listener,err:=net.Listen("tcp","127.0.0.1:0");if err!=nil {t.Fatal(err)}
 defer listener.Close()
 ingress:=Ingress{Key:[]byte("short"),Store:atomicStub{},Clock:time.Now}
 if err:=ServeIngress(context.Background(),listener,tls.Certificate{Certificate:[][]byte{{1}}},ingress);err==nil {t.Fatal("short key accepted")}
}
