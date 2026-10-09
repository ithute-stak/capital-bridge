"""Server-side subscription admission policy.

A requested company identifier is never sufficient proof of authorisation.
This module is called after Ithute JWT verification and current DB membership.
"""
from dataclasses import dataclass
from uuid import UUID

@dataclass(frozen=True)
class SubscriberIdentity:
    user_id: UUID
    company_id: UUID
    token_active: bool
    membership_active: bool

class SubscriptionDenied(PermissionError):
    pass

def authorize_subscription(identity:SubscriberIdentity,requested_company:UUID)->None:
    if not identity.token_active or not identity.membership_active:
        raise SubscriptionDenied("Active identity and company membership required")
    if not isinstance(requested_company,UUID) or requested_company!=identity.company_id:
        raise SubscriptionDenied("Requested company is not authorised")
