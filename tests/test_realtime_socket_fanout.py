import asyncio
import unittest
from unittest.mock import AsyncMock,patch
from uuid import uuid4
from api.realtime_fanout import RealtimeFanout
from api.realtime_websocket import websocket_session

class FanoutWebSocketTests(unittest.IsolatedAsyncioTestCase):
 async def test_company_event_sent_only_after_revalidation(self):
  bus=RealtimeFanout()
  company=uuid4();subject=uuid4();event=uuid4()
  socket=AsyncMock()
  async def fake_wait(coro,timeout):
   # Allow subscription to register before publishing.
   bus.publish_committed_event(company_id=company,event_id=event,
    event_type="invoice.issued",aggregate_id=uuid4())
   return await coro
  with patch("api.realtime_websocket.fetch_durable",return_value=([],None)),patch("api.realtime_websocket.asyncio.wait_for",side_effect=fake_wait),patch(
   "api.realtime_websocket.revalidate",side_effect=[True,False]) as auth:
   await websocket_session(socket,cookie="session",company_id=company,subject=subject,bus=bus)
  self.assertEqual(socket.send_json.call_count,1)
  self.assertEqual(socket.send_json.call_args.args[0]["event_id"],str(event))
  self.assertEqual(socket.close.call_args.kwargs["code"],1008)
  self.assertEqual(auth.call_count,2)
  self.assertNotIn(company,bus._subscribers)
 async def test_revoked_access_prevents_any_event_send(self):
  bus=RealtimeFanout();company=uuid4();subject=uuid4()
  socket=AsyncMock()
  async def fake_wait(coro,timeout):
   bus.publish_committed_event(company_id=company,event_id=uuid4(),
    event_type="payment.posted",aggregate_id=uuid4())
   return await coro
  with patch("api.realtime_websocket.asyncio.wait_for",side_effect=fake_wait),patch(
   "api.realtime_websocket.revalidate",return_value=False):
   await websocket_session(socket,cookie="revoked",company_id=company,subject=subject,bus=bus)
  socket.send_json.assert_not_called()
  self.assertEqual(socket.close.call_args.kwargs["code"],1008)
if __name__=="__main__":unittest.main()
