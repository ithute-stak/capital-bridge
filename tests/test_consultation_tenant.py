import os
import unittest
from unittest.mock import patch
from uuid import UUID
from api.consultation_tenant import consultation_company_id


class ConsultationTenantTests(unittest.TestCase):
    def test_server_only_company_id(self):
        company="aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
        with patch.dict(os.environ,{"CB_CONSULTATION_COMPANY_ID":company}):
            self.assertEqual(consultation_company_id(),UUID(company))

    def test_missing_invalid_and_nil_config_fail_closed(self):
        for value in ("","not-a-uuid","00000000-0000-0000-0000-000000000000"):
            with self.subTest(value=value),patch.dict(os.environ,{"CB_CONSULTATION_COMPANY_ID":value}):
                with self.assertRaises(RuntimeError):
                    consultation_company_id()

    def test_no_public_caller_fields_control_mapping(self):
        from pathlib import Path
        root=Path(__file__).resolve().parents[1]
        source=(root/"api"/"consultation_tenant.py").read_text()
        self.assertNotIn("request.headers",source)
        self.assertNotIn("request.query_params",source)
        self.assertNotIn("request.json",source)
        self.assertNotIn("company_id: UUID =",source)
