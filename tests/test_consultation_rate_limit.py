import unittest
from api.consultation_rate_limit import MAX_REQUESTS, IntakeRateLimitError, allow_intake_request

SECRET = "example-private-key-not-for-production-testing-only"

class FakeRedis:
    def __init__(self):
        self.counts = {}
    def eval(self, script, nkeys, key, ttl):
        self.counts[key] = self.counts.get(key, 0) + 1
        return self.counts[key]

class RateLimitTests(unittest.TestCase):
    def test_budget_exhaustion(self):
        db = FakeRedis()
        outcomes = [allow_intake_request(db, trusted_client_ip="127.0.0.1", secret=SECRET) for _ in range(MAX_REQUESTS+1)]
        self.assertEqual(outcomes, [True]*MAX_REQUESTS+[False])
        self.assertEqual(len(db.counts), 1)

    def test_isolation_by_ip(self):
        db=FakeRedis()
        self.assertTrue(allow_intake_request(db, trusted_client_ip="127.0.0.1", secret=SECRET))
        self.assertTrue(allow_intake_request(db, trusted_client_ip="127.0.0.2", secret=SECRET))
        self.assertEqual(len(db.counts), 2)

    def test_invalid_ip_denied(self):
        with self.assertRaises(IntakeRateLimitError):
            allow_intake_request(FakeRedis(), trusted_client_ip="invalid", secret=SECRET)

    def test_backend_error_denied(self):
        class Down:
            def eval(self, *args):
                raise RuntimeError("offline")
        with self.assertRaises(IntakeRateLimitError):
            allow_intake_request(Down(), trusted_client_ip="127.0.0.1", secret=SECRET)
