import unittest
from api.go_delivery_auth import canonical_delivery,sign_delivery
from hashlib import sha256
from hmac import new
EVENT={"version":1,"event_id":"evt-1","company_id":"tenant-1",
       "event_type":"payment.allocated","aggregate_id":"allocation-1"}
class GoDeliveryAuthTests(unittest.TestCase):
 def test_signing_is_stable_and_verifiable(self):
  key=b"a"*32
  body,sig=sign_delivery(EVENT,key=key)
  self.assertEqual(sig,new(key,body,sha256).hexdigest())
  self.assertEqual(body,canonical_delivery(dict(reversed(list(EVENT.items())))))
 def test_weak_key_and_extra_fields_fail(self):
  with self.assertRaises(ValueError):sign_delivery(EVENT,key=b"weak")
  with self.assertRaises(ValueError):canonical_delivery({**EVENT,"admin":True})
if __name__=="__main__":unittest.main()
