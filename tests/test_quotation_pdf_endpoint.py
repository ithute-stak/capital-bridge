import unittest
from unittest.mock import patch
from uuid import UUID
from fastapi.testclient import TestClient
from api.main import app, authenticate

COMPANY = UUID("11111111-1111-4111-8111-111111111111")
QUOTE = UUID("33333333-3333-4333-8333-333333333333")
USER = UUID("22222222-2222-4222-8222-222222222222")

class QuotationPDFEndpointTests(unittest.TestCase):
    def setUp(self):
        self.client=TestClient(app)
        self.url=f"/api/v1/companies/{COMPANY}/quotations/{QUOTE}/pdf"
    def tearDown(self):
        app.dependency_overrides.clear()
    def test_anonymous_download_denied(self):
        self.assertEqual(self.client.get(self.url).status_code,401)
    def test_missing_approved_logo_fails_closed(self):
        from api.quotation_download import trusted_logo
        with patch.dict("os.environ", {"CB_APPROVED_LOGO_PATH":""}, clear=True):
            with self.assertRaises(RuntimeError):
                trusted_logo()
    def test_publication_checks_company_before_query(self):
        app.dependency_overrides[authenticate]=lambda: USER
        from fastapi import HTTPException
        class Connection:
            def __enter__(self): return self
            def __exit__(self,*args): return False
            def transaction(self): return self
            def execute(self,*args): raise AssertionError("No quotation SQL allowed before company check")
        with patch("api.quotation_download.config",return_value=("issuer","aud","jwks","dsn")),patch(
            "api.quotation_download.psycopg.connect",return_value=Connection()
        ),patch("api.quotation_download.validate_company",side_effect=HTTPException(status_code=403)):
            self.assertEqual(self.client.get(self.url).status_code,403)

if __name__=="__main__": unittest.main()
