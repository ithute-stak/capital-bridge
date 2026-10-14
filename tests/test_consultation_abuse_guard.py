import unittest
from api.consultation_abuse_guard import validate_public_intake_headers, MAX_BODY_BYTES

class ConsultationAbuseGuardTests(unittest.TestCase):
    def test_valid_public_request_metadata(self):
        validate_public_intake_headers(origin="https://capitalbridge.co.ls",
            content_type="application/json; charset=utf-8", content_length=2048)

    def test_unapproved_origin_fails_closed(self):
        for origin in (None,"", "null", "http://capitalbridge.co.ls",
                       "https://evil.example", "https://capitalbridge.co.ls.evil.example"):
            with self.subTest(origin=origin), self.assertRaises(ValueError):
                validate_public_intake_headers(origin=origin,
                    content_type="application/json", content_length=1024)

    def test_content_type_and_size_enforced(self):
        cases=[("text/plain",512),(None,512),("application/json",0),
               ("application/json",MAX_BODY_BYTES+1),("application/json",None),
               ("application/json",-1),("application/json",True)]
        for content_type,size in cases:
            with self.subTest(content_type=content_type,size=size),self.assertRaises(ValueError):
                validate_public_intake_headers(origin="https://capitalbridge.co.ls",
                    content_type=content_type,content_length=size)
