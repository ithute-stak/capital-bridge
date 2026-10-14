import unittest
from api.erp_control_plane_db import control_plane_dsn


class ControlPlaneDBConfigTests(unittest.TestCase):
    def setUp(self):
        self.finance="postgresql://cb_finance:finance-secret@localhost:5432/finance"
        self.control="postgresql://cb_operator:operator-secret@localhost:5432/finance"

    def test_distinct_credential_and_role(self):
        self.assertEqual(control_plane_dsn({"CB_DATABASE_URL":self.finance,
            "CB_ERP_CONTROL_PLANE_DATABASE_URL":self.control}), self.control)

    def test_missing_and_reused_credential_denied(self):
        for dsn in ("", self.finance,
                    "postgresql://cb_finance:operator-secret@localhost/finance",
                    "postgresql://cb_operator:finance-secret@localhost/finance",
                    "postgresql://postgres:operator-secret@localhost/finance",
                    "postgresql://cb_erp_control_plane:operator-secret@localhost/finance",
                    "postgresql://cb_operator:operator-secret@localhost/finance?options=-c%20role%3Dpostgres"):
            with self.subTest(dsn=dsn), self.assertRaises(RuntimeError):
                control_plane_dsn({"CB_DATABASE_URL":self.finance,
                                  "CB_ERP_CONTROL_PLANE_DATABASE_URL":dsn})


if __name__ == "__main__":
    unittest.main()
