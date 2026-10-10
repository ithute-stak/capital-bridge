package main

import (
 "net/http"
 "net/http/httptest"
 "testing"
)
func TestParseReplayCursor(t *testing.T) {
 valid:="11111111-1111-4111-8111-111111111111"
 cases:=[]struct{value string;ok bool}{
  {"",true},{valid,true},{"malformed",false},{" "+valid,false},{valid+" ",false},
  {valid+","+valid,false},
 }
 for _,tc:=range cases {
  req:=httptest.NewRequest(http.MethodGet,"/events",nil)
  if tc.value!=""{req.Header.Set("Last-Event-ID",tc.value)}
  cursor,err:=ParseReplayCursor(req)
  if (err==nil)!=tc.ok{t.Errorf("cursor %q success=%v wanted %v",tc.value,err==nil,tc.ok)}
  if tc.value==valid && cursor.EventID!=valid{t.Fatal("valid cursor not preserved")}
 }
}
