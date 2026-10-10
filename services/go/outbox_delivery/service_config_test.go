package main
import (
 "os"
 "path/filepath"
 "testing"
)
func TestReadServiceConfigRejectsMissingParameters(t *testing.T){
 _,err:=ReadServiceConfig(func(string)string{return ""})
 if err==nil{t.Fatal("missing configuration accepted")}
}
func TestReadServiceConfigRequiresRestrictedTLSPostgres(t *testing.T){
 dir:=t.TempDir()
 cert:=filepath.Join(dir,"cert.pem");key:=filepath.Join(dir,"key.pem")
 if err:=os.WriteFile(cert,[]byte("test"),0600);err!=nil{t.Fatal(err)}
 if err:=os.WriteFile(key,[]byte("test"),0600);err!=nil{t.Fatal(err)}
 env:=map[string]string{
  "CB_GO_LISTEN":"127.0.0.1:8443",
  "CB_GO_COMPANY_ID":"22222222-2222-4222-8222-222222222222",
  "CB_GO_DATABASE_URL":"postgresql://cb_go_delivery@db.internal/capitalbridge?sslmode=verify-full",
  "CB_GO_TLS_CERT_FILE":cert,"CB_GO_TLS_KEY_FILE":key,
  "CB_GO_DELIVERY_HMAC_KEY":"12345678901234567890123456789012",
 }
 get:=func(s string)string{return env[s]}
 if _,err:=ReadServiceConfig(get);err!=nil{t.Fatal(err)}
 env["CB_GO_DATABASE_URL"]="postgresql://postgres@db.internal/capitalbridge?sslmode=disable"
 if _,err:=ReadServiceConfig(get);err==nil{t.Fatal("privileged or unencrypted connection accepted")}
}
