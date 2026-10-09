import unittest
from unittest.mock import Mock
from api.go_delivery_adapter import send_to_go
EVENT={"version":1,"event_id":"ev","company_id":"co","event_type":"payment.allocated","aggregate_id":"ag"}
class GoAdapterTests(unittest.TestCase):
 def test_signed_https_acceptance(self):
  client=Mock();client.post.return_value.status_code=202
  self.assertTrue(send_to_go(EVENT,url="https://go.internal.example/events",key=b"a"*32,client=client,clock=lambda:2000000))
  call=client.post.call_args
  self.assertIn("X-CB-Signature",call.kwargs["headers"])
  self.assertEqual(call.kwargs["headers"]["X-CB-Timestamp"],"2000000")
 def test_http_and_untrusted_credentials_fail(self):
  for url in ("http://go.internal/events","https://user:pass@go.internal/events"):
   with self.subTest(url=url),self.assertRaises(ValueError):
    send_to_go(EVENT,url=url,key=b"a"*32,client=Mock())
 def test_http_failure_not_acknowledged(self):
  client=Mock();client.post.return_value.status_code=503
  self.assertFalse(send_to_go(EVENT,url="https://go.internal/events",key=b"a"*32,client=client))
if __name__=="__main__":unittest.main()
