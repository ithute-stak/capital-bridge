package main

import (
 "net/http"
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
  req:=httptest.NewRequest(http.MethodGet,"https://capitalbridge.co.ls/events",nil)
  if c.origin!="" {req.Header.Set("Origin",c.origin)}
  if got:=validSSEOrigin(req,allowed);got!=c.ok {t.Errorf("origin %q got %v want %v",c.origin,got,c.ok)}
 }
 if validSSEOrigin(httptest.NewRequest("GET","/",nil),"http://capitalbridge.co.ls") {t.Fatal("insecure configured origin accepted")}
}
