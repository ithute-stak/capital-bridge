import unittest
from unittest.mock import Mock
from uuid import uuid4
from api.outbox_delivery_leases import claim_events,acknowledge_event,retry_event

class OutboxLeaseTests(unittest.TestCase):
 def test_claim_uses_skip_locked(self):
  db=Mock()
  db.execute.return_value.fetchall.return_value=[]
  self.assertEqual(claim_events(db,limit=10),[])
  self.assertIn("FOR UPDATE SKIP LOCKED",db.execute.call_args.args[0])
 def test_ack_requires_owned_lease(self):
  db=Mock()
  db.execute.return_value.fetchone.return_value=None
  self.assertFalse(acknowledge_event(db,event_id=uuid4(),claim_token=uuid4()))
  self.assertIn("claim_token=%s",db.execute.call_args.args[0])
 def test_retry_is_bounded_and_owned(self):
  db=Mock()
  db.execute.return_value.fetchone.return_value={"id":uuid4()}
  self.assertTrue(retry_event(db,event_id=uuid4(),claim_token=uuid4(),
                              attempts=30,error="downstream unavailable"))
  self.assertEqual(db.execute.call_args.args[1][0],3600)
  with self.assertRaises(ValueError):
   retry_event(db,event_id=uuid4(),claim_token=uuid4(),attempts=0,error="no")
if __name__=="__main__":unittest.main()
