package main

import "testing"

func TestParseCommitSignal(t *testing.T) {
 valid := `{"company_id":"11111111-1111-4111-8111-111111111111","event_id":"22222222-2222-4222-8222-222222222222"}`
 got,err := ParseCommitSignal(valid)
 if err!=nil || got.CompanyID!="11111111-1111-4111-8111-111111111111" {t.Fatalf("valid hint rejected: %+v %v",got,err)}
 bad := []string{
  "",
  `{}`,
  `{"company_id":"other","event_id":"22222222-2222-4222-8222-222222222222"}`,
  `{"company_id":"11111111-1111-4111-8111-111111111111","event_id":"invalid"}`,
  valid+"{}",
  `{"company_id":"11111111-1111-4111-8111-111111111111","event_id":"22222222-2222-4222-8222-222222222222","extra":true}`,
 }
 for _,s:=range bad { if _,err:=ParseCommitSignal(s);err==nil {t.Errorf("accepted invalid hint %q",s)} }
}
