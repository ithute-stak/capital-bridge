import unittest
from uuid import UUID
from api.realtime_subscription_policy import SubscriberIdentity, SubscriptionDenied, authorize_subscription

USER=UUID("11111111-1111-4111-8111-111111111111")
COMPANY=UUID("22222222-2222-4222-8222-222222222222")
OTHER=UUID("33333333-3333-4333-8333-333333333333")

class RealTimeSubscriptionTests(unittest.TestCase):
 def test_active_authorised_company_allowed(self):
  self.assertIsNone(authorize_subscription(SubscriberIdentity(USER,COMPANY,True,True),COMPANY))
 def test_cross_company_denied(self):
  with self.assertRaises(SubscriptionDenied):
   authorize_subscription(SubscriberIdentity(USER,COMPANY,True,True),OTHER)
 def test_expired_identity_denied(self):
  with self.assertRaises(SubscriptionDenied):
   authorize_subscription(SubscriberIdentity(USER,COMPANY,False,True),COMPANY)
 def test_revoked_membership_denied(self):
  with self.assertRaises(SubscriptionDenied):
   authorize_subscription(SubscriberIdentity(USER,COMPANY,True,False),COMPANY)
if __name__=="__main__": unittest.main()
