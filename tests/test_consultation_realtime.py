import os
import unittest
from unittest.mock import patch
from uuid import UUID
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect
from api.main import app
from api.consultation_events import consultation_channel,publish_consultation_change

COMPANY="11111111-1111-4111-8111-111111111111"
URL=f"/api/v1/staff/consultations/companies/{COMPANY}/events"

class ConsultationRealtimeTests(unittest.TestCase):
    def test_event_channel_is_company_scoped(self):
        self.assertIn(COMPANY,consultation_channel(UUID(COMPANY)))

    def test_websocket_requires_cookie(self):
        with patch.dict(os.environ,{"CB_PUBLIC_ORIGIN":"https://capitalbridge.co.ls"}):
            with self.assertRaises(WebSocketDisconnect):
                with TestClient(app).websocket_connect(URL,
                     headers={"Origin":"https://capitalbridge.co.ls"}):
                    pass

    def test_websocket_rejects_cross_origin_before_subscription(self):
        with patch.dict(os.environ,{"CB_PUBLIC_ORIGIN":"https://capitalbridge.co.ls"}):
            with self.assertRaises(WebSocketDisconnect):
                with TestClient(app).websocket_connect(URL,
                     headers={"Origin":"https://untrusted.example"}):
                    pass

    def test_no_pubsub_url_degrades_to_polling_fallback(self):
        with patch.dict(os.environ,{"CB_CONSULTATION_REDIS_URL":""}):
            self.assertFalse(publish_consultation_change(UUID(COMPANY)))
