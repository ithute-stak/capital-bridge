"""Cross-language event contract smoke tests for existing v1 prototypes.

These tests exercise Python coordination, Go envelope validation, and the Go
outbox CLI; none of these calls posts ledger entries or grants tenant access.
"""
import json
import subprocess
import unittest
from pathlib import Path

from services.python.workflow import FinanceEvent

ROOT = Path(__file__).resolve().parents[1]


def go_event(program: str, value: dict):
    cmd = ["go", "run", program] if program == "services/go/events/main.go" else [
        "go", "run", "services/go/outbox_delivery/main.go"
    ]
    env = None
    if program != "services/go/events/main.go":
        import os
        env = {**os.environ, "GO111MODULE": "off"}
    return subprocess.run(cmd, input=json.dumps(value), capture_output=True, text=True,
                          cwd=ROOT, env=env, timeout=90)


class CrossLanguageEventContract(unittest.TestCase):
    def test_python_to_go_v1(self):
        envelope = FinanceEvent("company-a", "invoice.issued", "invoice-1").as_envelope()
        result = go_event("services/go/events/main.go", envelope)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), envelope)

    def test_committed_outbox_event_round_trip(self):
        event = {"version": 1, "event_id": "evt-1", "company_id": "company-a",
                 "event_type": "payment.allocated", "aggregate_id": "allocation-1"}
        result = go_event("services/go/outbox_delivery/main.go", event)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), event)

    def test_outbox_rejects_extra_properties_and_unknown_type(self):
        base = {"version": 1, "event_id": "evt-1", "company_id": "company-a",
                "event_type": "invoice.issued", "aggregate_id": "invoice-1"}
        for change in ({"tenant_admin": True}, {"event_type": "admin.grant"},
                       {"version": 2}, {"company_id": ""}):
            with self.subTest(change=change):
                event = {**base, **change}
                result = go_event("services/go/outbox_delivery/main.go", event)
                self.assertNotEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
