import unittest
from unittest.mock import Mock
from uuid import UUID
from api.finance_outbox import enqueue_finance_event

COMPANY=UUID("11111111-1111-4111-8111-111111111111")
ENTITY=UUID("22222222-2222-4222-8222-222222222222")
class FinanceOutboxTests(unittest.TestCase):
 def test_enqueue_uses_caller_transaction_without_network(self):
  db=Mock()
  event_id=enqueue_finance_event(db,company_id=COMPANY,event_type="invoice.issued",
      aggregate_id=ENTITY,payload={"status":"issued"})
  self.assertIsInstance(event_id,UUID)
  self.assertEqual(db.execute.call_count,1)
  self.assertIn("INSERT INTO cb.finance_outbox",db.execute.call_args.args[0])
 def test_no_spoofed_event_types(self):
  with self.assertRaises(ValueError):
   enqueue_finance_event(Mock(),company_id=COMPANY,event_type="admin.grant",
       aggregate_id=ENTITY)
 def test_payload_is_json_object(self):
  with self.assertRaises(ValueError):
   enqueue_finance_event(Mock(),company_id=COMPANY,event_type="bank.matched",
       aggregate_id=ENTITY,payload=[])
if __name__=="__main__":unittest.main()
