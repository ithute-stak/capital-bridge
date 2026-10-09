package main

import (
 "crypto/hmac"
 "crypto/sha256"
 "encoding/hex"
 "errors"
 "strings"
)

// VerifyDeliveryMAC binds a complete canonical message to a private internal
// delivery key. Production transport additionally requires TLS and rotation.
func VerifyDeliveryMAC(key []byte, body []byte, hexSignature string) error {
 if len(key)<32 {return errors.New("delivery key too short")}
 sig,err:=hex.DecodeString(strings.TrimSpace(hexSignature))
 if err!=nil || len(sig)!=sha256.Size {return errors.New("invalid signature")}
 mac:=hmac.New(sha256.New,key)
 mac.Write(body)
 if !hmac.Equal(sig,mac.Sum(nil)) {return errors.New("signature mismatch")}
 return nil
}
