//go:build !capitalbridge_service

package main

import (
 "encoding/json"
 "fmt"
 "io"
 "os"
)

func main() {
 decoder:=json.NewDecoder(io.LimitReader(os.Stdin,65536))
 decoder.DisallowUnknownFields()
 var d Delivery
 if err:=decoder.Decode(&d);err!=nil {fmt.Fprintln(os.Stderr,"invalid JSON event");os.Exit(2)}
 if err:=validateDelivery(d);err!=nil {fmt.Fprintln(os.Stderr,err);os.Exit(2)}
 var extra interface{}
 if err:=decoder.Decode(&extra);err!=io.EOF {fmt.Fprintln(os.Stderr,"multiple event objects");os.Exit(2)}
 if err:=json.NewEncoder(os.Stdout).Encode(d);err!=nil {os.Exit(2)}
}
