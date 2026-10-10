//go:build capitalbridge_service

package main

import (
 "fmt"
 "os"
 _ "github.com/lib/pq"
)

func main() {
 if err:=StartIngressProcess("postgres");err!=nil {
  fmt.Fprintln(os.Stderr,"CapitalBridge ingress startup failed:",err)
  os.Exit(1)
 }
}
