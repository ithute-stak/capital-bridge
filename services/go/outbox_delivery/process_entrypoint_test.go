package main
import "testing"

func TestProcessEntryPointRequiresDatabaseDriver(t *testing.T){
 if err:=StartIngressProcess("");err==nil{
  t.Fatal("missing registered PostgreSQL driver accepted")
 }
}
func TestProcessEntryPointRejectsMissingEnvironment(t *testing.T){
 t.Setenv("CB_GO_COMPANY_ID","")
 if err:=StartIngressProcess("postgres");err==nil{
  t.Fatal("service started without company scope")
 }
}
