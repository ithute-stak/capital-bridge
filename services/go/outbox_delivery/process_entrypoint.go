package main

import (
 "context"
 "database/sql"
 "errors"
 "os"
 "os/signal"
 "syscall"
)

// StartIngressProcess is the managed-process entrypoint invoked with a
// registered PostgreSQL database/sql driver. It never logs credentials.
func StartIngressProcess(driver string) error {
 if driver=="" {return errors.New("registered PostgreSQL driver required")}
 cfg,err:=ReadServiceConfig(os.Getenv)
 if err!=nil{return err}
 ctx,stop:=signal.NotifyContext(context.Background(),syscall.SIGINT,syscall.SIGTERM)
 defer stop()
 return RunConfiguredIngress(ctx,cfg,func(dsn string)(*sql.DB,error){
  return sql.Open(driver,dsn)
 })
}
