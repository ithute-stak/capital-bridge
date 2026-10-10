import unittest
from api.realtime_readiness import readiness

class RealtimeReadinessTests(unittest.TestCase):
 def test_missing_all_prerequisites_fails_closed(self):
  result=readiness({})
  self.assertFalse(result["ready"])
  self.assertIn("end_to_end_runtime_not_verified",result["missing"])
 def test_partial_configuration_not_ready(self):
  self.assertFalse(readiness({"CB_PUBLIC_ORIGIN":"https://capitalbridge.co.ls"})["ready"])
 def test_verified_configuration(self):
  env={"CB_PUBLIC_ORIGIN":"https://capitalbridge.co.ls",
       "CB_DATABASE_URL":"postgresql://internal",
       "CB_SESSION_DATABASE_URL":"postgresql://sessions",
       "CB_GO_DELIVERY_URL":"https://go.internal/events",
       "CB_GO_DELIVERY_HMAC_KEY":"a"*32,
       "CB_REALTIME_WORKERS_ENABLED":"true",
       "CB_REALTIME_RUNTIME_VERIFIED":"true"}
  self.assertTrue(readiness(env)["ready"])
if __name__=="__main__":unittest.main()
