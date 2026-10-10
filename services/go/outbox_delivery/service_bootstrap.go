package main

import (
 "context"
 "crypto/tls"
 "database/sql"
 "errors"
 "net"
 "time"
)

// RunConfiguredIngress connects the validated pieces with a database opener.
// Only a restricted PostgreSQL driver should be passed as openDB; this package
// deliberately does not install one or read secrets beyond ReadServiceConfig.
func RunConfiguredIngress(ctx context.Context,cfg ServiceConfig,openDB func(string)(*sql.DB,error)) error {
 if ctx==nil || openDB==nil{return errors.New("context and database opener required")}
 if _,err:=ReadServiceConfig(func(k string)string{
  switch k {
  case "CB_GO_LISTEN":return cfg.Listen
  case "CB_GO_COMPANY_ID":return cfg.CompanyID
  case "CB_GO_DATABASE_URL":return cfg.DatabaseURL
  case "CB_GO_TLS_CERT_FILE":return cfg.CertificateFile
  case "CB_GO_TLS_KEY_FILE":return cfg.PrivateKeyFile
  case "CB_GO_DELIVERY_HMAC_KEY":return string(cfg.HMACKey)
  }
  return ""
 });err!=nil{return err}
 cert,err:=tls.LoadX509KeyPair(cfg.CertificateFile,cfg.PrivateKeyFile)
 if err!=nil{return errors.New("invalid TLS certificate or private key")}
 db,err:=openDB(cfg.DatabaseURL)
 if err!=nil{return errors.New("database connection initialization failed")}
 if db==nil{return errors.New("database opener returned nil")}
 defer db.Close()
 db.SetMaxOpenConns(8)
 db.SetMaxIdleConns(4)
 db.SetConnMaxLifetime(15*time.Minute)
 pingCtx,cancel:=context.WithTimeout(ctx,5*time.Second)
 defer cancel()
 if err=db.PingContext(pingCtx);err!=nil{return errors.New("restricted database connectivity failed")}
 listener,err:=net.Listen("tcp",cfg.Listen)
 if err!=nil{return err}
 defer listener.Close()
 store:=AtomicNotificationStore{DB:db,CompanyID:cfg.CompanyID}
 return ServeIngress(ctx,listener,cert,Ingress{Key:cfg.HMACKey,Store:store,Clock:time.Now})
}
