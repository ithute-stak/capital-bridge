package main

import (
 "context"
 "errors"
)

// SessionSubscriptionVerifier must resolve an opaque server-side session,
// check expiry/revocation, and verify live company membership.
// Implementations must not trust a browser-supplied company claim.
type SessionSubscriptionVerifier interface {
 VerifySubscriptionSession(ctx context.Context, sessionToken string) (SubscriptionPrincipal, error)
}

// AdmitSessionSubscription obtains the principal from a trusted verifier, then
// applies the company authorizer before registering with the tenant hub.
func AdmitSessionSubscription(ctx context.Context, hub *TenantHub, verifier SessionSubscriptionVerifier, auth CompanySubscriptionAuthorizer, sessionToken string, ch chan JournalNotification) (func(), error) {
 if verifier == nil || sessionToken == "" { return nil, errors.New("missing authenticated session") }
 if err := ctx.Err(); err != nil { return nil, err }
 principal, err := verifier.VerifySubscriptionSession(ctx, sessionToken)
 if err != nil { return nil, err }
 return AdmitTenantSubscription(ctx, hub, auth, principal, ch)
}
