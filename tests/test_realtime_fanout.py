import unittest
from uuid import uuid4
from api.realtime_fanout import RealtimeFanout

class RealtimeFanoutTests(unittest.TestCase):
 def test_only_matching_company_receives_event(self):
  bus=RealtimeFanout()
  a,b=uuid4(),uuid4()
  qa,qb=bus.subscribe(a),bus.subscribe(b)
  event=uuid4()
  self.assertEqual(bus.publish_committed_event(company_id=a,event_id=event,
    event_type="payment.allocated",aggregate_id=uuid4()),1)
  self.assertEqual(qa.get_nowait()["event_id"],str(event))
  self.assertTrue(qb.empty())
 def test_rejects_unapproved_event_type(self):
  bus=RealtimeFanout()
  with self.assertRaises(ValueError):
   bus.publish_committed_event(company_id=uuid4(),event_id=uuid4(),
      event_type="admin.grant",aggregate_id=uuid4())
 def test_overfull_subscriber_removed_not_cross_delivered(self):
  bus=RealtimeFanout(queue_size=1); company=uuid4()
  queue=bus.subscribe(company)
  bus.publish_committed_event(company_id=company,event_id=uuid4(),
    event_type="invoice.issued",aggregate_id=uuid4())
  self.assertEqual(bus.publish_committed_event(company_id=company,event_id=uuid4(),
    event_type="invoice.issued",aggregate_id=uuid4()),0)
  self.assertNotIn(company,bus._subscribers)
  self.assertEqual(queue.qsize(),1)
 def test_unsubscribe_cleans_up(self):
  bus=RealtimeFanout(); company=uuid4(); queue=bus.subscribe(company)
  bus.unsubscribe(company,queue)
  self.assertNotIn(company,bus._subscribers)
if __name__=="__main__": unittest.main()
