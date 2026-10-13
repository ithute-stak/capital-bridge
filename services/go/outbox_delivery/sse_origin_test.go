package main

import (
 "net/http"
 "crypto/tls"
 "net/http/httptest"
 "testing"
)

func TestSSEOriginPolicy(t *testing.T) {
 allowed:="https://capitalbridge.co.ls"
 cases:=[]struct{origin string;ok bool}{
  {"https://capitalbridge.co.ls",true},
  {"https://CAPITALBRIDGE.CO.LS",true},
  {"http://capitalbridge.co.ls",false},
  {"https://evil.example",false},
  {"https://capitalbridge.co.ls.evil.example",false},
  {"https://capitalbridge.co.ls/path",false},
  {"",false},
  {"null",false},
  {"https://capitalbridge.co.ls,https://evil.example",false},
 }
 for _,c:=range cases {
  req:=httptest.NewRequest(http.MethodGet,"http://capitalbridge.co.ls/events",nil)
  if c.origin!="" {req.Header.Set("Origin",c.origin)}
  if got:=validSSEOrigin(req,allowed);got!=c.ok {t.Errorf("origin %q got %v want %v",c.origin,got,c.ok)}
 }
 if validSSEOrigin(httptest.NewRequest("GET","/",nil),"http://capitalbridge.co.ls") {t.Fatal("insecure configured origin accepted")}
}

func TestSSEOriginlessSameHostRequiresTLS(t *testing.T) {
 req:=httptest.NewRequest(http.MethodGet,"http://capitalbridge.co.ls/api/v1/realtime/events",nil)
 req.Host="capitalbridge.co.ls"
 if validSSEOrigin(req,"https://capitalbridge.co.ls"){t.Fatal("originless without TLS accepted")}
 req.TLS=&tls.ConnectionState{}
 if !validSSEOrigin(req,"https://capitalbridge.co.ls"){t.Fatal("originless same-host TLS rejected")}
 req.Host="attacker.example"
 if validSSEOrigin(req,"https://capitalbridge.co.ls"){t.Fatal("originless foreign host accepted")}
 req.Host="capitalbridge.co.ls"
 req.Header.Set("X-Forwarded-Proto","https")
 req.TLS=nil
 if validSSEOrigin(req,"https://capitalbridge.co.ls"){t.Fatal("untrusted forwarded TLS accepted")}
}
