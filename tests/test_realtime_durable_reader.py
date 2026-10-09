import unittest
from unittest.mock import Mock
from uuid import uuid4
from datetime import datetime,timezone
from api.realtime_durable_reader import read_company_notifications

class DurableReaderTests(unittest.TestCase):
 def test_initial_cursor_is_company_scoped(self):
  db=Mock()
  db.execute.return_value.fetchone.return_value=None
  events,cursor=read_company_notifications(db,company_id=uuid4())
  self.assertEqual((events,cursor),([],None))
  self.assertIn("WHERE company_id=%s",db.execute.call_args.args[0])
 def test_paginated_reader_stays_inside_tenant(self):
  company=uuid4()
  cursor=(datetime.now(timezone.utc),uuid4())
  db=Mock()
  db.execute.return_value.fetchall.return_value=[{
   "id":uuid4(),"event_type":"invoice.issued",
   "aggregate_id":uuid4(),"received_at":datetime.now(timezone.utc)
  }]
  events,next_cursor=read_company_notifications(db,company_id=company,cursor=cursor)
  self.assertEqual(len(events),1)
  self.assertEqual(events[0]["company_id"],str(company))
  self.assertEqual(db.execute.call_args.args[1][0],company)
  self.assertIsNotNone(next_cursor)
 def test_invalid_limits_rejected(self):
  with self.assertRaises(ValueError):
   read_company_notifications(Mock(),company_id=uuid4(),limit=101)
if __name__=="__main__": unittest.main()
