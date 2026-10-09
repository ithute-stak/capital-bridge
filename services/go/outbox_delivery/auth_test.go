package main
import (
 "crypto/hmac"
 "crypto/sha256"
 "encoding/hex"
 "testing"
)
func TestVerifyDeliveryMAC(t *testing.T){
 key:=[]byte("12345678901234567890123456789012")
 body:=[]byte("{\"company_id\":\"company-a\",\"event_type\":\"payment.allocated\"}")
 m:=hmac.New(sha256.New,key);m.Write(body)
 sig:=hex.EncodeToString(m.Sum(nil))
 if err:=VerifyDeliveryMAC(key,body,sig);err!=nil{t.Fatal(err)}
 for _,tc:=range []struct{key,body []byte;sig string}{
  {key,[]byte("tampered"),sig},{key,body,"invalid"},
  {[]byte("short"),body,sig},
 }{if VerifyDeliveryMAC(tc.key,tc.body,tc.sig)==nil{t.Fatal("accepted invalid signature")}}
}
