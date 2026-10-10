package main

import (
 "context"
 "errors"
)

// SubscriptionPrincipal is established exclusively by a trusted server-side
// authentication component, never decoded from client-submitted company IDs.
type SubscriptionPrincipal struct {
 Subject string
 CompanyID string
}

// CompanySubscriptionAuthorizer verifies that an authenticated subject still
// belongs to the specified company. Implementations must consult trusted
// server-side identity/session data and reject inactive or revoked access.
type CompanySubscriptionAuthorizer interface {
 AuthorizeSubscription(context.Context, SubscriptionPrincipal) error
}

// AdmitTenantSubscription enforces a server-side authorization gate before
// allowing a connection to join the tenant hub.
func AdmitTenantSubscription(ctx context.Context, hub *TenantHub, auth CompanySubscriptionAuthorizer, principal SubscriptionPrincipal, ch chan JournalNotification) (func(), error) {
 if hub == nil || auth == nil || principal.Subject == "" || !signalUUID.MatchString(principal.CompanyID) {
  return nil, errors.New("subscription not configured or identity invalid")
 }
 if err := ctx.Err(); err != nil { return nil, err }
 if err := auth.AuthorizeSubscription(ctx, principal); err != nil { return nil, err }
 return hub.RegisterAuthorized(principal.CompanyID, ch)
}
