import unittest
from unittest.mock import patch,MagicMock
from uuid import UUID
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect
from api.main import app

COMPANY=UUID("22222222-2222-4222-8222-222222222222")
USER=UUID("11111111-1111-4111-8111-111111111111")
PATH=f"/api/v1/companies/{COMPANY}/realtime/ws"
class HandshakeTests(unittest.TestCase):
 def setUp(self): self.client=TestClient(app)
 def test_missing_origin_rejected(self):
  with patch.dict("os.environ",{"CB_PUBLIC_ORIGIN":"https://capitalbridge.co.ls"}):
   with self.assertRaises(WebSocketDisconnect):
    with self.client.websocket_connect(PATH): pass
 def test_missing_session_rejected(self):
  with patch.dict("os.environ",{"CB_PUBLIC_ORIGIN":"https://capitalbridge.co.ls"}):
   with self.assertRaises(WebSocketDisconnect):
    with self.client.websocket_connect(PATH,headers={"origin":"https://capitalbridge.co.ls"}):pass
 def test_cross_origin_rejected_even_with_cookie(self):
  self.client.cookies.set("cb_session","untrusted")
  with patch.dict("os.environ",{"CB_PUBLIC_ORIGIN":"https://capitalbridge.co.ls"}):
   with self.assertRaises(WebSocketDisconnect):
    with self.client.websocket_connect(PATH,headers={"origin":"https://attacker.example"}):pass
 def test_valid_session_still_needs_company_membership(self):
  self.client.cookies.set("cb_session","verified-cookie")
  db=MagicMock()
  db.__enter__.return_value=db
  db.transaction.return_value.__enter__.return_value=db
  with patch.dict("os.environ",{"CB_PUBLIC_ORIGIN":"https://capitalbridge.co.ls"}),patch(
   "api.realtime_websocket.LoginDatabaseSettings.from_environment"),patch(
   "api.realtime_websocket.authentication_connection",return_value=MagicMock()),patch(
   "api.realtime_websocket.resolve",return_value=USER),patch(
   "api.realtime_websocket.config",return_value=("issuer","audience","jwks","dsn")),patch(
   "api.realtime_websocket.psycopg.connect",return_value=db),patch(
   "api.realtime_websocket.validate_company") as validate:
   async def no_wait(_): return None
   with patch("api.realtime_websocket.asyncio.sleep",side_effect=no_wait):
    with self.client.websocket_connect(PATH,headers={"origin":"https://capitalbridge.co.ls"}) as ws:
     self.assertEqual(ws.receive_json()["type"],"heartbeat")
   self.assertGreaterEqual(validate.call_count,2)
if __name__=="__main__":unittest.main()
