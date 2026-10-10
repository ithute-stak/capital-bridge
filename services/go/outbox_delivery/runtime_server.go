package main

import (
 "context"
 "crypto/tls"
 "errors"
 "net"
 "net/http"
 "time"
)

// ServeIngress runs the authenticated ingress handler on a TLS listener.
// A caller must inject a company-scoped atomic PostgreSQL store and supply
// certificates; this does not provide or provision production credentials.
func ServeIngress(ctx context.Context, listener net.Listener, cert tls.Certificate, ingress Ingress) error {
 if ctx == nil || listener == nil || len(cert.Certificate) == 0 {
  return errors.New("TLS listener, certificate and context required")
 }
 if len(ingress.Key) < 32 || ingress.Clock == nil || ingress.Store == nil {
  return errors.New("ingress credentials and atomic store required")
 }
 if _, ok := ingress.Store.(interface{ ClaimEvent(Delivery)(bool,error) }); !ok {
  return errors.New("atomic durable delivery store required")
 }
 mux := http.NewServeMux()
 mux.Handle("/internal/events", ingress)
 server := &http.Server{
  Handler:mux, ReadHeaderTimeout:5*time.Second, ReadTimeout:10*time.Second,
  WriteTimeout:15*time.Second, IdleTimeout:30*time.Second,
  MaxHeaderBytes:8192,
  TLSConfig:&tls.Config{MinVersion:tls.VersionTLS12, Certificates:[]tls.Certificate{cert}},
 }
 tlsListener := tls.NewListener(listener,server.TLSConfig)
 done:=make(chan struct{})
 go func(){
  select {
  case <-ctx.Done():
   shutdownCtx,cancel:=context.WithTimeout(context.Background(),5*time.Second)
   defer cancel()
   _=server.Shutdown(shutdownCtx)
  case <-done:
  }
 }()
 err:=server.Serve(tlsListener)
 close(done)
 if errors.Is(err,http.ErrServerClosed) {return nil}
 return err
}
