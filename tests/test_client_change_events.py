import unittest
from unittest.mock import Mock
from uuid import uuid4
from api.finance_outbox import enqueue_finance_event
from api.realtime_fanout import RealtimeFanout

class ClientEventTests(unittest.TestCase):
 def test_create_and_update_events_are_enqueueable(self):
  db=Mock()
  for kind in ("client.created","client.updated"):
   event=enqueue_finance_event(db,company_id=uuid4(),event_type=kind,aggregate_id=uuid4())
   self.assertIsNotNone(event)
  self.assertEqual(db.execute.call_count,2)
 def test_company_isolation_for_client_change(self):
  bus=RealtimeFanout();a=uuid4();b=uuid4();q1=bus.subscribe(a);q2=bus.subscribe(b)
  bus.publish_committed_event(company_id=a,event_id=uuid4(),event_type="client.updated",aggregate_id=uuid4())
  self.assertEqual(q1.get_nowait()["event_type"],"client.updated")
  self.assertTrue(q2.empty())
if __name__=="__main__":unittest.main()
