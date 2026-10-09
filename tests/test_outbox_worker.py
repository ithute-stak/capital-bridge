import unittest
from unittest.mock import patch
from uuid import uuid4
from api.outbox_worker import deliver_batch

class FakeDB:
 def __enter__(self): return self
 def __exit__(self,*args): return False
 def transaction(self): return self

class OutboxWorkerTests(unittest.TestCase):
 def setUp(self):
  self.row=dict(id=uuid4(),claim_token=uuid4(),company_id=uuid4(),
                aggregate_id=uuid4(),schema_version=1,event_type="payment.allocated",attempts=1)
 def test_success_requires_downstream_ack_before_db_ack(self):
  calls=[]
  def downstream(e):
   calls.append("delivered")
   self.assertEqual(e["event_id"],str(self.row["id"]))
   return True
  def ack(*args,**kwargs):
   calls.append("acknowledged")
   return True
  with patch("api.outbox_worker.claim_events",return_value=[self.row]),patch(
   "api.outbox_worker.acknowledge_event",side_effect=ack),patch(
   "api.outbox_worker.retry_event") as retry:
   result=deliver_batch(lambda:FakeDB(),downstream)
  self.assertEqual(calls,["delivered","acknowledged"])
  self.assertEqual(result["acknowledged"],1)
  retry.assert_not_called()
 def test_failed_delivery_does_not_acknowledge(self):
  with patch("api.outbox_worker.claim_events",return_value=[self.row]),patch(
   "api.outbox_worker.acknowledge_event") as ack,patch(
   "api.outbox_worker.retry_event",return_value=True) as retry:
   result=deliver_batch(lambda:FakeDB(),lambda _:False)
  self.assertEqual(result["retried"],1)
  ack.assert_not_called()
  retry.assert_called_once()
 def test_exception_only_retries_without_exposing_secret(self):
  def fail(_): raise RuntimeError("sensitive-credential")
  with patch("api.outbox_worker.claim_events",return_value=[self.row]),patch(
   "api.outbox_worker.acknowledge_event") as ack,patch(
   "api.outbox_worker.retry_event",return_value=True) as retry:
   self.assertEqual(deliver_batch(lambda:FakeDB(),fail)["retried"],1)
  self.assertNotIn("sensitive-credential",retry.call_args.kwargs["error"])
  ack.assert_not_called()
 def test_expired_lease_cannot_count_as_delivered(self):
  with patch("api.outbox_worker.claim_events",return_value=[self.row]),patch(
   "api.outbox_worker.acknowledge_event",return_value=False):
   result=deliver_batch(lambda:FakeDB(),lambda _:True)
  self.assertEqual(result["lost_lease"],1)
  self.assertEqual(result["acknowledged"],0)
if __name__=="__main__": unittest.main()
