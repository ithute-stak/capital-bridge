package main
import (
 "context"
 "database/sql"
 "errors"
 "testing"
)
func TestConfiguredIngressFailsClosedWithoutOpener(t *testing.T){
 err:=RunConfiguredIngress(context.Background(),ServiceConfig{},nil)
 if err==nil{t.Fatal("missing database opener accepted")}
}
func TestConfiguredIngressRejectsUnconfiguredRuntimeBeforeDatabase(t *testing.T){
 called:=false
 err:=RunConfiguredIngress(context.Background(),ServiceConfig{},func(string)(*sql.DB,error){
  called=true
  return nil,errors.New("must not be called")
 })
 if err==nil{t.Fatal("missing runtime config accepted")}
 if called{t.Fatal("database access attempted before validation")}
}
