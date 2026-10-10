package main

import (
 "errors"
 "net"
 "net/url"
 "os"
 "strings"
)

type ServiceConfig struct {
 Listen string
 CompanyID string
 DatabaseURL string
 CertificateFile string
 PrivateKeyFile string
 HMACKey []byte
}

func ReadServiceConfig(getenv func(string)string)(ServiceConfig,error){
 cfg:=ServiceConfig{
  Listen:getenv("CB_GO_LISTEN"),
  CompanyID:getenv("CB_GO_COMPANY_ID"),
  DatabaseURL:getenv("CB_GO_DATABASE_URL"),
  CertificateFile:getenv("CB_GO_TLS_CERT_FILE"),
  PrivateKeyFile:getenv("CB_GO_TLS_KEY_FILE"),
  HMACKey:[]byte(getenv("CB_GO_DELIVERY_HMAC_KEY")),
 }
 if !uuidPattern.MatchString(cfg.CompanyID) {return cfg,errors.New("invalid scoped company")}
 host,port,err:=net.SplitHostPort(cfg.Listen)
 if err!=nil || host=="" || port=="" {return cfg,errors.New("explicit service bind address required")}
 if len(cfg.HMACKey)<32{return cfg,errors.New("HMAC key must be at least 32 bytes")}
 if cfg.CertificateFile=="" || cfg.PrivateKeyFile=="" {return cfg,errors.New("TLS files required")}
 if _,err=os.Stat(cfg.CertificateFile);err!=nil{return cfg,errors.New("TLS certificate unavailable")}
 if _,err=os.Stat(cfg.PrivateKeyFile);err!=nil{return cfg,errors.New("TLS private key unavailable")}
 dsn,err:=url.Parse(cfg.DatabaseURL)
 if err!=nil || (dsn.Scheme!="postgres" && dsn.Scheme!="postgresql") ||
  dsn.Hostname()=="" || dsn.User==nil || dsn.User.Username()!="cb_go_delivery" {
   return cfg,errors.New("restricted PostgreSQL role required")
 }
 if strings.ToLower(dsn.Query().Get("sslmode"))!="verify-full" {return cfg,errors.New("PostgreSQL verify-full TLS required")}
 return cfg,nil
}
